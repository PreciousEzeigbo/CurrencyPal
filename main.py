from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from utils.currency_api import convert_currency, get_rates_to_naira
from models.a2a import (
    JSONRPCRequest, JSONRPCResponse, TaskResult, TaskStatus,
    Artifact, MessagePart, A2AMessage, MessageConfiguration
)
import re
from datetime import datetime
from uuid import uuid4
import logging
import httpx
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CurrencyPal", 
    description="A2A compliant currency conversion agent 💱",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


async def send_webhook_notification(url: str, token: str, response_text: str, original_request_id: str, task_id: str):
    """Send webhook notification to Telex.im for non-blocking requests"""
    try:
        # Telex.im expects a JSON-RPC request with message object structure
        webhook_payload = {
            "jsonrpc": "2.0",
            "id": original_request_id,
            "method": "message/send",
            "params": {
                "message": {
                    "kind": "message",
                    "role": "assistant",
                    "parts": [
                        {
                            "kind": "text",
                            "text": response_text
                        }
                    ],
                    "taskId": task_id
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        logger.info(f"📦 Webhook payload: {webhook_payload}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=webhook_payload, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ Webhook notification sent successfully")
            else:
                logger.error(f"❌ Webhook notification failed: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"💥 Webhook notification error: {str(e)}", exc_info=True)


async def process_message(user_text: str) -> str:
    """
    Core message processing logic - shared by all endpoints.
    Takes user text input and returns response text.
    """
    if not user_text:
        return "Please say something! 😊 Try 'convert 10 USD to NGN' or 'help' to see what I can do."
    
    user_text_lower = user_text.strip().lower()
    
    # 1. Greetings
    greeting_patterns = r'\b(hi|hello|hey|greetings|good\s*(morning|afternoon|evening)|howdy|sup|yo)\b'
    if re.search(greeting_patterns, user_text_lower):
        return ("Hello! 👋 I'm CurrencyPal, your friendly currency conversion assistant! 💱\n\n"
                "I can help you:\n"
                "• Convert currencies: 'convert 100 USD to NGN'\n"
                "• Check rates: 'show rates to NGN' or 'USD rate'\n"
                "• Get help: 'help' or 'what can you do'\n\n"
                "What would you like to know?")
    
    # 2. Help requests
    help_patterns = r'\b(help|assist|what can you do|commands|how to use|guide|instructions|info|about)\b'
    if re.search(help_patterns, user_text_lower):
        return ("🌟 CurrencyPal Help Guide 🌟\n\n"
                "Here's what I can do:\n\n"
                "💱 **Currency Conversion:**\n"
                "• 'convert 50 USD to NGN'\n"
                "• 'how much is 100 EUR in GBP'\n"
                "• 'what is 25.50 CAD in NGN'\n"
                "• Just type: '100 USD to NGN'\n\n"
                "📊 **Exchange Rates:**\n"
                "• 'show rates to NGN' (multiple currencies)\n"
                "• 'USD rate' or 'EUR to NGN rate' (single currency)\n"
                "• 'rates' (default: USD, EUR, GBP, JPY, CAD)\n\n"
                "💬 **Other:**\n"
                "• Say 'hi' for a greeting\n"
                "• Say 'help' to see this message\n\n"
                "I support 160+ currencies with real-time rates! 🌍")
    
    # 3. Thank you responses
    thanks_patterns = r'\b(thanks|thank you|thx|appreciate|cheers)\b'
    if re.search(thanks_patterns, user_text_lower):
        return ("You're very welcome! 😊 Happy to help with currency conversions anytime! 💱\n"
                "Need anything else? Just ask!")
    
    # 4. Currency Conversion - Multiple patterns
    conversion_match = None
    
    conversion_match = re.search(
        r'convert\s+(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+to\s+([a-zA-Z]{3})',
        user_text_lower
    )
    
    if not conversion_match:
        conversion_match = re.search(
            r'how\s+much\s+is\s+(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+in\s+([a-zA-Z]{3})',
            user_text_lower
        )
    
    if not conversion_match:
        conversion_match = re.search(
            r'what\s+is\s+(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+(?:in|to)\s+([a-zA-Z]{3})',
            user_text_lower
        )
    
    if not conversion_match:
        conversion_match = re.search(
            r'(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+(?:to|in)\s+([a-zA-Z]{3})',
            user_text_lower
        )
    
    if not conversion_match:
        help_convert_match = re.search(
            r'(?:help|need|want).*?convert(?:ing)?.*?(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})',
            user_text_lower
        )
        if help_convert_match:
            amount_str, from_currency = help_convert_match.groups()
            amount = float(amount_str.replace(',', '.'))
            
            if 'naira' in user_text_lower or 'ngn' in user_text_lower:
                result = await convert_currency(from_currency, 'NGN', amount)
                
                if "error" in result:
                    return (f"Oops! 😕 {result['error']}\n\n"
                           f"Please check:\n"
                           f"• Currency codes are valid (e.g., USD, EUR, NGN)\n"
                           f"• The amount is a positive number\n\n"
                           f"Try: 'convert {amount} {from_currency.upper()} to NGN'")
                
                return f"✅ {result['message']}"
    
    if conversion_match and len(conversion_match.groups()) >= 3:
        amount_str, from_currency, to_currency = conversion_match.groups()
        amount = float(amount_str.replace(',', '.'))
        
        result = await convert_currency(from_currency, to_currency, amount)
        
        if "error" in result:
            return (f"Oops! 😕 {result['error']}\n\n"
                   f"Please check:\n"
                   f"• Currency codes are valid (e.g., USD, EUR, NGN)\n"
                   f"• The amount is a positive number\n\n"
                   f"Try: 'convert 10 USD to NGN'")
        
        return f"✅ {result['message']}"
    
    # 5. Single currency rate check
    single_rate_match = re.search(
        r'\b([a-zA-Z]{3})\s+(?:rate|to\s+ngn)',
        user_text_lower
    )
    
    if not single_rate_match:
        single_rate_match = re.search(
            r'(?:rate|price)\s+(?:of|for)\s+([a-zA-Z]{3})',
            user_text_lower
        )
    
    if single_rate_match:
        currency = single_rate_match.group(1).upper()
        rates = await get_rates_to_naira([currency])
        
        if "error" in rates:
            return (f"Sorry, I couldn't fetch the {currency} rate right now. 😕\n"
                   f"Error: {rates['error']}\n\n"
                   f"Try again in a moment or check the currency code.")
        
        if currency in rates:
            return f"💱 Current rate: {rates[currency]['formatted']}"
        else:
            return (f"Sorry, I couldn't find the rate for {currency}. 🤔\n"
                   f"Make sure it's a valid 3-letter currency code (e.g., USD, EUR, GBP).")
    
    # 6. Multiple rates to Naira
    if re.search(r'\b(rate|rates|exchange)\b', user_text_lower) and \
       re.search(r'\b(ngn|naira|show|all|list)\b', user_text_lower):
        rates = await get_rates_to_naira()
        
        if "error" in rates:
            return (f"Sorry, couldn't fetch rates right now. 😕\n"
                   f"Error: {rates['error']}\n\n"
                   f"Please try again in a moment.")
        
        formatted = "\n".join([f"💱 {rates[cur]['formatted']}" for cur in rates.keys()])
        return f"Here are current rates to Nigerian Naira 🇳🇬:\n\n{formatted}"
    
    # 7. General rate inquiry
    if re.search(r'\b(rates?|exchange)\b', user_text_lower) and \
       not re.search(r'\b([a-zA-Z]{3})\b', user_text_lower):
        rates = await get_rates_to_naira()
        
        if "error" in rates:
            return f"Sorry, couldn't fetch rates right now. 😕\nPlease try again in a moment."
        
        formatted = "\n".join([f"💱 {rates[cur]['formatted']}" for cur in rates.keys()])
        return f"Here are current rates to Nigerian Naira 🇳🇬:\n\n{formatted}"
    
    # 8. Fallback
    return ("Hmm, I'm not sure I understood that. 🤔\n\n"
           "Here's what I can help with:\n"
           "• **Convert currency:** 'convert 50 USD to NGN' or just '50 USD to NGN'\n"
           "• **Check rates:** 'USD rate' or 'show rates to NGN'\n"
           "• **Get help:** Type 'help'\n\n"
           "What would you like to do?")


@app.get("/")
async def root():
    return {
        "message": "Welcome to CurrencyPal! 💱",
        "version": "1.0.0",
        "protocol": "A2A (JSON-RPC 2.0)",
        "endpoints": {
            "a2a": "POST /a2a/agent/currencyAgent (JSON-RPC 2.0)",
            "convert": "/convert?from=USD&to=NGN&amount=50",
            "rates": "/rates?currencies=USD,EUR,GBP",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "CurrencyPal",
        "version": "1.0.0",
        "protocol": "A2A (JSON-RPC 2.0)",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/a2a/agent/currencyAgent")
async def a2a_agent(request: Request):
    """
    A2A (Agent-to-Agent) protocol endpoint - JSON-RPC 2.0 compliant
    
    Supports two methods:
    1. message/send - Send a single message
    2. execute - Execute with message history and context
    
    Request format:
    {
        "jsonrpc": "2.0",
        "id": "request-id",
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "role": "user",
                "parts": [{"kind": "text", "text": "convert 100 USD to NGN"}]
            }
        }
    }
    """
    try:
        # Parse request body
        body = await request.json()
        logger.info(f"📨 Received A2A request: {body}")

        # Validate JSON-RPC request
        if body.get("jsonrpc") != "2.0" or "id" not in body:
            logger.error("❌ Invalid JSON-RPC request")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request: jsonrpc must be '2.0' and id is required"
                    }
                }
            )

        # Parse and validate request
        rpc_request = JSONRPCRequest(**body)

        # Extract messages
        messages = []
        context_id = None
        task_id = None
        config = None

        if rpc_request.method == "message/send":
            messages = [rpc_request.params.message]
            config = rpc_request.params.configuration
        elif rpc_request.method == "execute":
            messages = rpc_request.params.messages
            context_id = rpc_request.params.contextId
            task_id = rpc_request.params.taskId

        # Extract user text from messages
        user_text = ""
        for message in messages:
            if message.role == "user":
                for part in message.parts:
                    if part.kind == "text" and part.text:
                        user_text = part.text
                        break
                if user_text:
                    break

        logger.info(f"💬 Processing message: {user_text}")

        # Process the message
        response_text = await process_message(user_text)
        logger.info(f"✅ Generated response: {response_text[:100]}...")

        # Generate IDs
        context_id = context_id or str(uuid4())
        task_id = task_id or str(uuid4())

        # Build A2A response message
        response_message = A2AMessage(
            role="agent",
            parts=[MessagePart(kind="text", text=response_text)],
            taskId=task_id
        )

        # Build task result
        task_result = TaskResult(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state="completed",
                message=response_message
            ),
            artifacts=[],
            history=messages + [response_message]
        )

        # Build response
        response_data = {
            "jsonrpc": "2.0",
            "id": rpc_request.id,
            "result": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text/plain",
                                "text": response_text
                            }
                        ]
                    }
                ]
            }
        }

        # Check if we need to send a webhook notification (non-blocking mode)
        if config and hasattr(config, 'pushNotificationConfig') and config.pushNotificationConfig:
            webhook_url = config.pushNotificationConfig.url
            webhook_token = config.pushNotificationConfig.token
            
            logger.info(f"📤 Sending webhook notification to {webhook_url}")
            
            # Send webhook in background (don't wait)
            asyncio.create_task(send_webhook_notification(
                webhook_url, 
                webhook_token, 
                response_text,
                rpc_request.id,
                task_id
            ))
        
        logger.info(f"📤 Sending Telex A2A response format")
        return response_data

    except ValueError as e:
        logger.error(f"💥 Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if "body" in locals() else None,
                "error": {
                    "code": -32602,
                    "message": "Invalid params",
                    "data": {"details": str(e)}
                }
            }
        )
    except Exception as e:
        logger.error(f"💥 Internal error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if "body" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"details": str(e)}
                }
            }
        )


# Legacy endpoints for backward compatibility
@app.get("/convert")
async def convert(
    from_currency: str = Query(..., min_length=3, max_length=3),
    to_currency: str = Query(..., min_length=3, max_length=3),
    amount: float = Query(1.0, gt=0)
):
    """Convert one currency to another"""
    result = await convert_currency(from_currency, to_currency, amount)
    return result


@app.get("/rates")
async def rates(
    currencies: str = Query("USD,EUR,GBP,JPY,CAD")
):
    """Get multiple currency rates compared to NGN"""
    currency_list = [c.strip().upper() for c in currencies.split(",")]
    rates = await get_rates_to_naira(currency_list)

    if "error" in rates:
        return {"message": "Couldn't fetch live rates right now.", "error": rates["error"]}

    formatted = [rates[cur]["formatted"] for cur in rates.keys()]
    raw_rates = {cur: rates[cur]["rate"] for cur in rates.keys()}

    return {
        "base": "NGN",
        "rates": raw_rates,
        "formatted_rates": formatted,
        "message": " | ".join(formatted)
    }


if __name__ == "__main__":
    import uvicorn
    port = 8000
    logger.info(f"🚀 Starting CurrencyPal on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from utils.currency_api import convert_currency, get_rates_to_naira
import re
from datetime import datetime
import logging
import httpx
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CurrencyPal", 
    description="Currency conversion agent for Telex 💱",
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


async def process_message(user_text: str) -> str:
    """Core message processing logic"""
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
                "💱 **Currency Conversion:**\n"
                "• 'convert 50 USD to NGN'\n"
                "• 'how much is 100 EUR in GBP'\n"
                "• Just type: '100 USD to NGN'\n\n"
                "📊 **Exchange Rates:**\n"
                "• 'show rates' or 'USD rate'\n\n"
                "I support 160+ currencies with real-time rates! 🌍")
    
    # 3. Thank you responses
    thanks_patterns = r'\b(thanks|thank you|thx|appreciate|cheers)\b'
    if re.search(thanks_patterns, user_text_lower):
        return "You're very welcome! 😊 Happy to help with currency conversions anytime! 💱"
    
    # 4. Currency Conversion
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
            r'(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+(?:to|in)\s+([a-zA-Z]{3})',
            user_text_lower
        )
    
    if conversion_match and len(conversion_match.groups()) >= 3:
        amount_str, from_currency, to_currency = conversion_match.groups()
        amount = float(amount_str.replace(',', '.'))
        
        result = await convert_currency(from_currency, to_currency, amount)
        
        if "error" in result:
            return f"Oops! 😕 {result['error']}\n\nTry: 'convert 10 USD to NGN'"
        
        return f"✅ {result['message']}"
    
    # 5. Single currency rate
    single_rate_match = re.search(r'\b([a-zA-Z]{3})\s+rate', user_text_lower)
    
    if single_rate_match:
        currency = single_rate_match.group(1).upper()
        rates = await get_rates_to_naira([currency])
        
        if "error" in rates:
            return f"Sorry, couldn't fetch the {currency} rate right now. 😕"
        
        if currency in rates:
            return f"💱 Current rate: {rates[currency]['formatted']}"
    
    # 6. Multiple rates
    if re.search(r'\b(rates?|exchange)\b', user_text_lower):
        rates = await get_rates_to_naira()
        
        if "error" in rates:
            return "Sorry, couldn't fetch rates right now. 😕"
        
        formatted = "\n".join([f"💱 {rates[cur]['formatted']}" for cur in rates.keys()])
        return f"Here are current rates to Nigerian Naira 🇳🇬:\n\n{formatted}"
    
    # 7. Fallback
    return ("Hmm, I'm not sure I understood that. 🤔\n\n"
           "Try:\n"
           "• 'convert 50 USD to NGN'\n"
           "• 'USD rate'\n"
           "• 'help'")


@app.get("/")
async def root():
    return {
        "message": "Welcome to CurrencyPal! 💱",
        "version": "1.0.0",
        "endpoints": {
            "a2a": "POST /a2a/agent/currencyAgent",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "CurrencyPal",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/a2a/agent/currencyAgent")
async def a2a_agent(request: Request):
    """
    Telex A2A endpoint - matches the working format from logs
    """
    body = None # Initialize body to None
    request_id = str(uuid4()) # Default request_id

    try:
        body = await request.json()
        logger.info(f"📨 REQUEST: {body}")

        # Auto-generate ID if missing
        request_id = body.get("id", str(uuid4()))

        # Validate JSON-RPC version
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=200, # Return 200 with error object
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32600,
                        "message": "Invalid JSON-RPC version. Must be '2.0'."
                    }
                }
            )

        params = body.get("params", {})
        message = params.get("message", {})
        
        # Extract user text - prioritize the most recent user message from the conversation history
        user_text = ""
        parts = message.get("parts", [])

        # Iterate through parts in reverse to find the most recent user input
        for part in reversed(parts):
            if part.get("kind") == "data":
                data_entries = part.get("data", [])
                if isinstance(data_entries, list) and data_entries:
                    # Iterate through data entries in reverse to find the last user text
                    for entry in reversed(data_entries):
                        if isinstance(entry, dict) and entry.get("kind") == "text" and entry.get("text"):
                            # Clean HTML tags if present
                            cleaned_text = re.sub(r'<[^>]+>', '', entry["text"]).strip()
                            if cleaned_text:
                                user_text = cleaned_text
                                break
                    if user_text:
                        break # Found user text in data, stop searching
            elif part.get("kind") == "text":
                # Fallback to the last 'text' part if no user input found in 'data'
                current_text = part.get("text", "").strip()
                if current_text and not user_text: # Only use if user_text is still empty
                    # Apply the "split by convert" or "last 100 chars" logic
                    if "convert" in current_text.lower():
                        sentences = current_text.lower().split("convert")
                        if len(sentences) > 1:
                            user_text = "convert" + sentences[-1].strip()
                        else:
                            user_text = current_text
                    elif len(current_text) > 100:
                        user_text = current_text[-100:].strip()
                    else:
                        user_text = current_text
            if user_text:
                break # Found user text, stop searching
        
        logger.info(f"💬 EXTRACTED: {user_text}")

        # Process message
        response_text = await process_message(user_text)
        logger.info(f"✅ RESPONSE: {response_text[:100]}...")

        # Build A2A compliant TaskResult structure
        a2a_result = {
            "id": request_id,
            "contextId": request_id, # Assuming contextId can be the same as request_id for simplicity
            "status": {
                "state": "completed",
                "message": {
                    "kind": "message",
                    "role": "agent",
                    "parts": [
                        {
                            "kind": "text",
                            "text": response_text
                        }
                    ],
                    "messageId": str(uuid4()) # Generate a new messageId
                }
            },
            "artifacts": [],
            "history": []
        }

        # Get configuration
        config = params.get("configuration", {})
        push_config = config.get("pushNotificationConfig")
        is_blocking = config.get("blocking", True) # Default to blocking if not specified
        
        logger.info(f"🔍 Mode: blocking={is_blocking}, has_webhook={bool(push_config)}")

        if push_config and not is_blocking:
            # Non-blocking mode - send full A2A result to webhook
            webhook_url = push_config.get("url")
            token = push_config.get("token")
            
            if webhook_url:
                logger.info(f"📤 Sending full A2A result to webhook: {webhook_url}")
                
                # Construct the webhook payload with the A2A message
                webhook_payload = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "message/send",
                    "params": {
                        "message": a2a_result["status"]["message"], # This is the actual message to be sent
                        "configuration": config
                    }
                }

                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        headers = {
                            "Content-Type": "application/json"
                        }
                        if token:
                            headers["Authorization"] = f"Bearer {token}"
                        
                        webhook_response = await client.post(
                            webhook_url,
                            json=webhook_payload,
                            headers=headers
                        )
                        logger.info(f"✅ Webhook sent: {webhook_response.status_code}")
                        logger.info(f"📨 Webhook response: {webhook_response.text}")
                except Exception as e:
                    logger.error(f"❌ Webhook error: {str(e)}", exc_info=True)
                
                # Return acknowledgment for non-blocking mode
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"status": "processing"}
                }
        
        # Blocking mode or no webhook config - return full A2A result directly
        logger.info(f"↩️ Returning direct A2A result (blocking mode or no webhook)")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": a2a_result
        }

    except Exception as e:
        logger.error(f"💥 ERROR: {str(e)}", exc_info=True)
        # Return 200 with error object for internal errors
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "id": request_id, # Use the generated or extracted request_id
                "error": {
                    "code": -32603,
                    "message": "Internal error processing request",
                    "data": {"details": str(e)}
                }
            }
        )


# Legacy endpoints
@app.get("/convert")
async def convert(
    from_currency: str = Query(..., min_length=3, max_length=3),
    to_currency: str = Query(..., min_length=3, max_length=3),
    amount: float = Query(1.0, gt=0)
):
    result = await convert_currency(from_currency, to_currency, amount)
    return result


@app.get("/rates")
async def rates(currencies: str = Query("USD,EUR,GBP,JPY,CAD")):
    currency_list = [c.strip().upper() for c in currencies.split(",")]
    rates = await get_rates_to_naira(currency_list)

    if "error" in rates:
        return {"error": rates["error"]}

    formatted = [rates[cur]["formatted"] for cur in rates.keys()]
    raw_rates = {cur: rates[cur]["rate"] for cur in rates.keys()}

    return {
        "base": "NGN",
        "rates": raw_rates,
        "formatted_rates": formatted
    }


if __name__ == "__main__":
    import uvicorn
    port = 8000
    logger.info(f"🚀 Starting CurrencyPal on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
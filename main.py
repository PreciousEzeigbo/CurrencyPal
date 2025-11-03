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
    try:
        body = await request.json()
        logger.info(f"📨 REQUEST: {body}")

        # Validate JSON-RPC
        if body.get("jsonrpc") != "2.0" or "id" not in body:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    }
                }
            )

        request_id = body.get("id")
        params = body.get("params", {})
        message = params.get("message", {})
        
        # Extract user text - handle Telex's concatenated format
        user_text = ""
        parts = message.get("parts", [])
        
        if parts:
            # Get the first part's text
            first_part = parts[0]
            if first_part.get("kind") == "text":
                all_text = first_part.get("text", "")
                
                # Split by "convert" and take the last one
                if "convert" in all_text.lower():
                    sentences = all_text.lower().split("convert")
                    if len(sentences) > 1:
                        user_text = "convert" + sentences[-1].strip()
                    else:
                        user_text = all_text.strip()
                else:
                    # Take just the last 100 characters if no "convert"
                    user_text = all_text[-100:].strip()
        
        logger.info(f"💬 EXTRACTED: {user_text}")

        # Process message
        response_text = await process_message(user_text)
        logger.info(f"✅ RESPONSE: {response_text[:100]}...")

        # Get configuration
        config = params.get("configuration", {})

        # Build response message in A2A format
        response_message = {
            "kind": "message",
            "role": "agent",
            "parts": [
                {
                    "kind": "text",
                    "text": response_text
                }
            ],
            "messageId": str(uuid4())
        }

        # Build complete JSON-RPC response for webhook
        webhook_payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "message/send",
            "params": {
                "message": response_message,
                "configuration": config
            }
        }

        # Check if we need to send to webhook (non-blocking mode)
        push_config = config.get("pushNotificationConfig")
        is_blocking = config.get("blocking", True)
        
        logger.info(f"🔍 Mode: blocking={is_blocking}, has_webhook={bool(push_config)}")
        
        if push_config and not is_blocking:
            # Non-blocking mode - send to webhook
            webhook_url = push_config.get("url")
            token = push_config.get("token")
            
            if webhook_url:
                logger.info(f"📤 Sending to webhook: {webhook_url}")
                
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        headers = {
                            "Content-Type": "application/json"
                        }
                        
                        # Add Bearer token if provided
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
                
                # Return acknowledgment
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"status": "processing"}
                }
        
        # Blocking mode - return response directly (simplified format)
        logger.info(f"↩️ Returning direct response (blocking mode)")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "messages": [
                    {
                        "role": "agent",
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

    except Exception as e:
        logger.error(f"💥 ERROR: {str(e)}", exc_info=True)
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
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from utils.currency_api import convert_currency, get_rates_to_naira
import re
from datetime import datetime

app = FastAPI(
    title="CurrencyPal", 
    description="A simple currency conversion agent 💱",
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
    
    # Pattern 1: "convert X FROM to TO"
    conversion_match = re.search(
        r'convert\s+(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+to\s+([a-zA-Z]{3})',
        user_text_lower
    )
    
    # Pattern 2: "how much is X FROM in TO"
    if not conversion_match:
        conversion_match = re.search(
            r'how\s+much\s+is\s+(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+in\s+([a-zA-Z]{3})',
            user_text_lower
        )
    
    # Pattern 3: "what is X FROM in TO"
    if not conversion_match:
        conversion_match = re.search(
            r'what\s+is\s+(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+(?:in|to)\s+([a-zA-Z]{3})',
            user_text_lower
        )
    
    # Pattern 4: "X FROM to TO" (simple)
    if not conversion_match:
        conversion_match = re.search(
            r'(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})\s+(?:to|in)\s+([a-zA-Z]{3})',
            user_text_lower
        )
    
    # Pattern 5: "help convert X FROM" (with naira context)
    if not conversion_match:
        help_convert_match = re.search(
            r'(?:help|need|want).*?convert(?:ing)?.*?(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3})',
            user_text_lower
        )
        if help_convert_match:
            amount_str, from_currency = help_convert_match.groups()
            amount = float(amount_str.replace(',', '.'))
            
            # Check if "naira" or "NGN" is mentioned
            if 'naira' in user_text_lower or 'ngn' in user_text_lower:
                result = await convert_currency(from_currency, 'NGN', amount)
                
                if "error" in result:
                    return (f"Oops! 😕 {result['error']}\n\n"
                           f"Please check:\n"
                           f"• Currency codes are valid (e.g., USD, EUR, NGN)\n"
                           f"• The amount is a positive number\n\n"
                           f"Try: 'convert {amount} {from_currency.upper()} to NGN'")
                
                return f"✅ {result['message']}"
    
    # Process standard conversion patterns
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
        "endpoints": {
            "convert": "/convert?from=USD&to=NGN&amount=50",
            "rates": "/rates?currencies=USD,EUR,GBP",
            "chat": "POST /chat with {text: 'your message'}",
            "a2a": "POST /a2a/agent/currencyAgent (Telex.im integration)",
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
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/convert")
async def convert(
    from_currency: str = Query(..., min_length=3, max_length=3, description="Currency code (e.g., USD)"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Currency code (e.g., NGN)"),
    amount: float = Query(1.0, gt=0, description="Amount to convert")
):
    """
    Convert one currency to another using live exchange rates
    
    Example: /convert?from=USD&to=NGN&amount=100
    """
    result = await convert_currency(from_currency, to_currency, amount)
    return result

@app.post("/chat")
async def chat_agent(message: dict):
    """
    Chat endpoint for CurrencyPal - A conversational currency conversion assistant
    
    Example inputs: 
    - {"text": "hi"} or {"text": "hello"}
    - {"text": "convert 10 usd to ngn"}
    - {"text": "how much is 50 EUR in NGN"}
    - {"text": "show rates"} or {"text": "usd rate"}
    - {"text": "help"} or {"text": "what can you do"}
    """
    user_text = message.get("text", "").strip()
    response_text = await process_message(user_text)
    return {"response": response_text}


@app.post("/a2a/agent/currencyAgent")
async def a2a_agent(request: dict):
    """
    A2A (Agent-to-Agent) protocol endpoint for Telex.im integration
    
    This endpoint follows the A2A protocol format expected by Telex.im
    
    Expected request format:
    {
        "text": "user message",
        "conversationId": "unique-conversation-id",
        "userId": "user-id" (optional),
        "metadata": {} (optional)
    }
    
    Returns:
    {
        "text": "agent response",
        "conversationId": "same-conversation-id",
        "agentName": "CurrencyPal",
        "timestamp": "ISO timestamp"
    }
    """
    try:
        # Extract the user's message and conversation metadata
        user_message = request.get("text", "")
        conversation_id = request.get("conversationId", "")
        user_id = request.get("userId", "")
        
        # Validate input
        if not user_message:
            return {
                "text": "I didn't receive any message. Please try again! 😊",
                "conversationId": conversation_id,
                "agentName": "CurrencyPal",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "empty_message"
            }
        
        # Process the message using shared logic
        response_text = await process_message(user_message)
        
        # Return in A2A protocol format
        return {
            "text": response_text,
            "conversationId": conversation_id,
            "agentName": "CurrencyPal",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "userId": user_id,
                "responseType": "success"
            }
        }
        
    except Exception as e:
        # Error handling with proper A2A format
        return {
            "text": f"I encountered an error processing your request. Please try again! 🔧\n\nError: {str(e)}",
            "conversationId": request.get("conversationId", ""),
            "agentName": "CurrencyPal",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "responseType": "error",
                "errorDetails": str(e)
            }
        }


@app.get("/rates")
async def rates(
    currencies: str = Query("USD,EUR,GBP,JPY,CAD", description="Comma-separated currency codes (e.g., USD,EUR,GBP)")
):
    """
    Get multiple currency rates compared to NGN
    
    Example: /rates?currencies=USD,EUR,GBP,CAD
    """
    currency_list = [c.strip().upper() for c in currencies.split(",")]
    rates = await get_rates_to_naira(currency_list)

    if "error" in rates:
        return {"message": "Couldn't fetch live rates right now.", "error": rates["error"]}

    # Extract formatted messages for display
    formatted = [rates[cur]["formatted"] for cur in rates.keys()]
    
    # Also provide raw rates for programmatic use
    raw_rates = {cur: rates[cur]["rate"] for cur in rates.keys()}

    return {
        "base": "NGN",
        "rates": raw_rates,
        "formatted_rates": formatted,
        "message": " | ".join(formatted)
    }


# Optional: Handle A2A requests at root endpoint as well
@app.post("/")
async def root_a2a(request: dict):
    """Handle A2A requests at root endpoint if Telex calls base URL"""
    # Check if this looks like an A2A request
    if "text" in request or "conversationId" in request:
        return await a2a_agent(request)
    
    # Otherwise return info
    return await root()


if __name__ == "__main__":
    import uvicorn
    port = 8000
    print(f"🚀 Starting CurrencyPal on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
import httpx
from typing import Dict, List, Optional, Any

# Using exchangerate-api.com - free tier, no API key required
BASE_RATES_URL = "https://api.exchangerate-api.com/v4/latest"

# Currency symbols mapping
CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥",
    "NGN": "₦", "CAD": "C$", "AUD": "A$", "CHF": "Fr", "INR": "₹",
    "KRW": "₩", "BRL": "R$", "ZAR": "R", "RUB": "₽", "MXN": "$",
    "SGD": "S$", "HKD": "HK$", "SEK": "kr", "NOK": "kr", "DKK": "kr",
    "PLN": "zł", "TRY": "₺", "THB": "฿", "IDR": "Rp", "MYR": "RM",
    "PHP": "₱", "AED": "د.إ", "SAR": "﷼", "EGP": "E£", "ILS": "₪",
}


def get_currency_symbol(currency_code: str) -> str:
    """
    Get currency symbol or return currency code if symbol not found
    
    Args:
        currency_code: 3-letter currency code (e.g., USD, EUR)
    
    Returns:
        Currency symbol or currency code if not found
    """
    return CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code.upper())


def format_amount(amount: float, currency_code: str) -> str:
    """
    Format amount with commas and currency symbol
    
    Args:
        amount: Numerical amount to format
        currency_code: 3-letter currency code
    
    Returns:
        Formatted string (e.g., "$1,234.56")
    """
    symbol = get_currency_symbol(currency_code)
    # Format with commas for thousands
    formatted_number = f"{amount:,.2f}"
    
    # For currencies that typically show symbol after (like EUR in some locales)
    # we'll keep it simple and show symbol before for consistency
    return f"{symbol}{formatted_number}"


async def convert_currency(
    from_currency: str, 
    to_currency: str, 
    amount: float
) -> Dict[str, Any]:
    """
    Fetch conversion rate and result from exchangerate-api.com
    
    Args:
        from_currency: Source currency code (e.g., USD)
        to_currency: Target currency code (e.g., NGN)
        amount: Amount to convert
    
    Returns:
        Dictionary containing conversion results or error message
    """
    try:
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_RATES_URL}/{from_curr}")
            response.raise_for_status()  # Raise exception for bad status codes
            data = response.json()
            
    except httpx.ConnectTimeout:
        return {
            "error": "Connection timed out. The exchange rate service is not responding."
        }
    except httpx.ReadTimeout:
        return {
            "error": "Request timed out. The exchange rate service took too long to respond."
        }
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}: Unable to fetch exchange rates."
        }
    except httpx.RequestError as e:
        return {
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "error": f"An unexpected error occurred: {str(e)}"
        }

    # Check if the response contains rates
    if "rates" not in data:
        return {
            "error": f"Invalid response from exchange rate service for {from_curr}"
        }
    
    if to_curr not in data["rates"]:
        return {
            "error": f"Currency {to_curr} not found. Please check the currency code."
        }

    rate = data["rates"][to_curr]
    result = amount * rate

    # Format amounts with currency symbols and commas
    formatted_from_amount = format_amount(amount, from_curr)
    formatted_to_amount = format_amount(result, to_curr)
    formatted_rate = f"{rate:,.4f}".rstrip('0').rstrip('.')  # Remove trailing zeros

    return {
        "from": from_curr,
        "to": to_curr,
        "amount": amount,
        "rate": round(rate, 4),
        "converted": round(result, 2),
        "formatted_amount": formatted_from_amount,
        "formatted_converted": formatted_to_amount,
        "message": f"{formatted_from_amount} = {formatted_to_amount} 💱 (Rate: 1 {from_curr} = {formatted_rate} {to_curr})"
    }


async def get_rates_to_naira(
    currencies: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch live exchange rates for a list of currencies to NGN
    
    Args:
        currencies: List of currency codes to fetch rates for.
                   Defaults to ["USD", "EUR", "GBP", "JPY", "CAD"]
    
    Returns:
        Dictionary with currency rates or error message
    """
    if currencies is None:
        currencies = ["USD", "EUR", "GBP", "JPY", "CAD"]

    try:
        # Fetch rates from NGN base
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_RATES_URL}/NGN")
            response.raise_for_status()
            data = response.json()
            
    except httpx.ConnectTimeout:
        return {
            "error": "Connection timed out. The exchange rate service is not responding."
        }
    except httpx.ReadTimeout:
        return {
            "error": "Request timed out. The exchange rate service took too long to respond."
        }
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}: Unable to fetch exchange rates."
        }
    except httpx.RequestError as e:
        return {
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "error": f"An unexpected error occurred: {str(e)}"
        }

    if "rates" not in data:
        return {"error": "Failed to fetch rates from exchange service"}

    rates = data.get("rates", {})
    result = {}

    for cur in currencies:
        cur_upper = cur.upper()
        if cur_upper in rates:
            # Convert: 1 CUR = X NGN means we need to invert (1/rate)
            rate = 1 / rates[cur_upper] if rates[cur_upper] != 0 else None
            if rate:
                result[cur_upper] = {
                    "rate": round(rate, 2),
                    "formatted": f"{get_currency_symbol(cur_upper)}1 = {get_currency_symbol('NGN')}{rate:,.2f}"
                }

    return result


async def get_supported_currencies() -> List[str]:
    """
    Fetch list of all supported currency codes
    
    Returns:
        List of currency codes
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_RATES_URL}/USD")
            response.raise_for_status()
            data = response.json()
            
            if "rates" in data:
                return sorted(data["rates"].keys())
            return []
            
    except Exception:
        # Return common currencies if API fails
        return ["USD", "EUR", "GBP", "JPY", "NGN", "CAD", "AUD", "CHF", "CNY", "INR"]
#!/usr/bin/env python3
"""
CurrencyPal API Client Example

This script demonstrates how to interact with the CurrencyPal API
programmatically using Python.

Make sure the CurrencyPal server is running before executing this script:
    uvicorn main:app --reload
"""

import requests
import json
from typing import Dict, Any


# API Base URL
BASE_URL = "http://127.0.0.1:8000"


def print_response(title: str, response: Dict[str, Any]) -> None:
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    print()


def test_root() -> None:
    """Test the root endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print_response("Root Endpoint", response.json())


def test_conversion() -> None:
    """Test currency conversion"""
    # Example 1: Convert USD to NGN
    response = requests.get(
        f"{BASE_URL}/convert",
        params={
            "from_currency": "USD",
            "to_currency": "NGN",
            "amount": 100
        }
    )
    print_response("Convert $100 USD to NGN", response.json())
    
    # Example 2: Convert EUR to GBP
    response = requests.get(
        f"{BASE_URL}/convert",
        params={
            "from_currency": "EUR",
            "to_currency": "GBP",
            "amount": 50
        }
    )
    print_response("Convert €50 EUR to GBP", response.json())


def test_rates() -> None:
    """Test exchange rates endpoint"""
    # Example 1: Default currencies
    response = requests.get(f"{BASE_URL}/rates")
    print_response("Default Rates to NGN", response.json())
    
    # Example 2: Custom currencies
    response = requests.get(
        f"{BASE_URL}/rates",
        params={"currencies": "USD,EUR,GBP,CAD,AUD"}
    )
    print_response("Custom Rates to NGN", response.json())


def test_chat() -> None:
    """Test chat endpoint with various inputs"""
    test_messages = [
        "Hello",
        "help",
        "convert 50 USD to NGN",
        "how much is 100 EUR in GBP",
        "USD rate",
        "show rates to NGN",
        "thanks",
    ]
    
    for message in test_messages:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"text": message}
        )
        print_response(f"Chat: '{message}'", response.json())


def interactive_chat() -> None:
    """Interactive chat session with CurrencyPal"""
    print("\n" + "="*60)
    print("  Interactive CurrencyPal Chat")
    print("  Type 'exit' or 'quit' to end the session")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("CurrencyPal: Goodbye! 👋\n")
                break
            
            if not user_input:
                continue
            
            response = requests.post(
                f"{BASE_URL}/chat",
                json={"text": user_input}
            )
            
            data = response.json()
            print(f"CurrencyPal: {data.get('response', 'No response')}\n")
            
        except KeyboardInterrupt:
            print("\n\nCurrencyPal: Goodbye! 👋\n")
            break
        except Exception as e:
            print(f"Error: {e}\n")


def main():
    """Main function to run all examples"""
    print("\n" + "="*60)
    print("  CurrencyPal API Client Examples")
    print("="*60)
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("\n❌ Error: CurrencyPal server is not responding properly")
            print("   Make sure the server is running: uvicorn main:app --reload\n")
            return
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to CurrencyPal server")
        print("   Make sure the server is running: uvicorn main:app --reload\n")
        return
    
    print("\n✅ Connected to CurrencyPal API\n")
    
    # Run examples
    print("\n" + "#"*60)
    print("# 1. Testing Root Endpoint")
    print("#"*60)
    test_root()
    
    print("\n" + "#"*60)
    print("# 2. Testing Currency Conversion")
    print("#"*60)
    test_conversion()
    
    print("\n" + "#"*60)
    print("# 3. Testing Exchange Rates")
    print("#"*60)
    test_rates()
    
    print("\n" + "#"*60)
    print("# 4. Testing Chat Endpoint")
    print("#"*60)
    test_chat()
    
    # Ask if user wants interactive chat
    print("\n" + "="*60)
    response = input("Would you like to try interactive chat? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        interactive_chat()
    
    print("\n✅ All examples completed!\n")


if __name__ == "__main__":
    main()

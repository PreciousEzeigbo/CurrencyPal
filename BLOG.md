# Building CurrencyPal: A Real-Time Currency Conversion AI Agent 💱

## Introduction

Have you ever needed to quickly convert currencies while chatting with someone online? That's exactly the problem I set out to solve with **CurrencyPal** — an intelligent AI agent that provides real-time currency conversions and exchange rates directly within the Telex.im messaging platform.

In this article, I'll walk you through the technical journey of building CurrencyPal, from initial concept to deployment, including the challenges I faced integrating with the Agent-to-Agent (A2A) protocol and how I overcame them. This project showcases practical applications of Python, FastAPI, natural language processing, and API integrations in building production-ready AI agents.lding CurrencyPal: A Real-time Currency Conversion Agent for Telex.im

## Introduction

This blog post details the development and integration of CurrencyPal, an AI agent designed to provide real-time currency conversions and exchange rates on the Telex.im platform. Built as part of HNG Backend Internship Stage 3, this project showcases the process of designing an intelligent system, handling integrations with the A2A protocol, and structuring Python code for a robust agent.

## What is CurrencyPal?

CurrencyPal is an intelligent conversational agent designed to make currency conversion effortless. Users can interact with it naturally, and it understands commands like:

✅ **Currency Conversions**: "convert 50 USD to NGN" or "how much is 100 EUR in GBP?"  
✅ **Exchange Rates**: "USD rate" or "show me current rates"  
✅ **Natural Conversations**: Responds to greetings, help requests, and provides friendly, emoji-enriched responses

### Tech Stack

The agent is built using modern Python technologies:

- **FastAPI**: For creating a high-performance, async web API
- **Regular Expressions**: For parsing natural language user inputs
- **httpx**: For making async HTTP requests to currency exchange APIs
- **Pydantic**: For data validation and ensuring protocol compliance
- **A2A Protocol**: For seamless integration with the Telex.im platform

## Architecture & Technical Implementation

### System Design

The application follows a clean, modular architecture:

**`main.py`** — The heart of the application

- FastAPI application setup
- `process_message()` function for natural language understanding
- `/a2a/agent/currencyAgent` endpoint for platform integration

**`models/a2a.py`** — Protocol compliance layer

- Pydantic models defining the A2A (Agent-to-Agent) protocol
- JSON-RPC 2.0 message structures
- Ensures type safety and validation

**`utils/currency_api.py`** — External service integration

- Handles API calls to fetch real-time exchange rates
- Currency conversion logic

### Natural Language Processing with `process_message`

The `process_message()` function is CurrencyPal's brain. It's an asynchronous function that analyzes user input and determines intent using regex pattern matching:

**Intent Detection:**

- **Greetings** → Welcomes users and explains capabilities
- **Help Requests** → Provides usage instructions
- **Gratitude** → Acknowledges thank-you messages
- **Currency Conversion** → Extracts amount and currency codes, performs conversion
- **Rate Queries** → Fetches and displays current exchange rates
- **Fallback** → Handles unrecognized inputs gracefully

This approach allows for natural, conversational interactions without requiring complex NLP models, keeping the agent lightweight and fast.

## The Challenge: Integrating with the A2A Protocol

### Understanding the Problem

The `/a2a/agent/currencyAgent` endpoint serves as the communication bridge between CurrencyPal and Telex.im. It's a POST endpoint that receives JSON-RPC 2.0 requests and must respond in the exact format expected by the platform.

During initial deployment, I encountered a frustrating issue: the agent connected successfully, but users only saw "Converting 50 USD to NGN... Please wait a moment!" followed by "Error while streaming." The actual conversion results never appeared.

### The Debugging Journey

**Initial Hypothesis**: I suspected the issue was with how the agent handled `blocking` and `pushNotificationConfig` parameters. Perhaps it was sending acknowledgments instead of complete results?

**First Attempt**: I simplified the response logic to directly return the messages array. Result? The streaming error persisted, and I still saw `{"status": "processing"}` in the logs.

This told me something important: **the problem wasn't with my logic — it was with the response format itself.**

### The Breakthrough: Protocol Compliance

The solution came from carefully reviewing the A2A protocol specification in `models/a2a.py`. I discovered that:

1. **JSONRPCResponse** expects a `result` field of type `TaskResult`
2. **TaskResult** must contain:
   - A `status` object with a `state` field (e.g., "completed")
   - The actual response in `status.message.parts[0].text`
   - Proper `id` and `contextId` fields

I wasn't just returning data — I needed to wrap it in the proper protocol structure!

### The Implementation

Here's what I did to fix it:

```python
# 1. Ensured proper imports
from uuid import uuid4

# 2. Constructed a proper TaskResult object
task_result = TaskResult(
    id=request_id,
    contextId=request_id,
    status=Status(
        state="completed",
        message=A2AMessage(
            parts=[MessagePart(text=response_text)]
        )
    )
)

# 3. Returned A2A-compliant JSON-RPC response
return JSONRPCResponse(
    jsonrpc="2.0",
    id=request_id,
    result=task_result
)
```

I also fixed syntax errors in `models/a2a.py` related to the `A2AMessage` class definition.

### Results

✅ The agent now returns fully A2A-compliant responses  
✅ Logs confirm successful workflow execution  
✅ Currency conversions are properly formatted and delivered

While a minor streaming error persists on the platform side (likely a client-side issue), the agent itself is robust and fulfills its contract perfectly.

## Key Takeaways

Building CurrencyPal taught me several valuable lessons:

### 1. **Protocol Compliance is Non-Negotiable**

When integrating with external platforms, understanding and strictly adhering to API specifications is crucial. The difference between a working and non-working integration often comes down to exact data structure formatting.

### 2. **Read the Schema, Not Just the Docs**

The breakthrough came from examining the Pydantic models themselves. Sometimes the schema definition is more informative than high-level documentation.

### 3. **Debugging Requires Patience and Methodical Thinking**

Rather than randomly changing code, I systematically:

- Analyzed error messages
- Reviewed protocol specifications
- Made targeted changes
- Validated results at each step

### 4. **Simple Solutions Can Be Powerful**

CurrencyPal uses regex for NLP instead of complex ML models, proving that the right tool for the job isn't always the most sophisticated one.

## Conclusion

CurrencyPal demonstrates how modern Python frameworks like FastAPI, combined with proper protocol integration, can create powerful, production-ready AI agents. The project showcases the entire development lifecycle — from initial implementation to debugging complex integration issues and achieving full protocol compliance.

Whether you're building chatbots, API integrations, or AI agents, the principles remain the same: understand your requirements, follow specifications meticulously, and debug systematically.

---

**Want to try CurrencyPal?** Check out the [GitHub repository](https://github.com/PreciousEzeigbo/CurrencyPal) for the complete source code.

**Have questions or suggestions?** Feel free to reach out or leave a comment below. I'd love to hear about your experiences building AI agents!

---

_This project was built as part of the HNG Internship program. Interested in joining? Learn more at [HNG Internship](https://hng.tech/internship) and explore opportunities for [hire Node.js developers](https://hng.tech/hire/nodejs-developers)._

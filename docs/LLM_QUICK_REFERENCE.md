# LLM Quick Reference

This guide shows how to use the unified LLM client across providers: Gemini, OpenAI (and Azure OpenAI), Mistral, and Ollama.

## Installation

The LLM module ships with faciliter-lib (Python 3.12+). Provider SDKs are optional per provider:

- Gemini: google-genai
- OpenAI/Azure: openai>=1.0
- Mistral: mistralai
- Ollama (local): ollama
- Optional: pydantic (for structured outputs)

Install only what you need for your provider.

## Quick Start

```python
from faciliter_lib import create_ollama_client, create_gemini_client, create_client_from_env

# Local Ollama
ollama = create_ollama_client(model="llama3.2", temperature=0.7)
print(ollama.chat("Hello!")["content"])

# Google Gemini
gemini = create_gemini_client(api_key="your-key", model="gemini-1.5-flash")
print(gemini.chat("Explain quantum computing briefly")["content"])

# OpenAI (or Azure OpenAI) via environment
# Set OPENAI_API_KEY (and OPENAI_BASE_URL for Azure) then:
openai_client = create_client_from_env("openai")
print(openai_client.chat("One-line haiku about clouds")["content"])

# Mistral via environment (set MISTRAL_API_KEY)
mistral = create_client_from_env("mistral")
print(mistral.chat("Summarize this in 10 words: LLMs are great.")["content"])
```

## What You Get

- Unified chat API across providers
- Env-based configuration helpers
- OpenAI-style tools (function calling) where supported
- Structured JSON output via Pydantic JSON Schema (provider support varies)
- Conversation history support
- Robust orchestrator under the hood (retries, rate limits, circuit breaker, tracing)

## Response Shape

client.chat(...) returns a dict:

```python
{
    "content": "text or structured data",  # If structured_output is used and supported, content is parsed JSON (dict/list)
    "structured": bool,                     # True when structured_output is active and provider returned JSON
    "tool_calls": [                         # OpenAI-style tool calls when supported
        {"type": "function", "function": {"name": "...", "arguments": "{...}"}}
    ],
    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0}
}
```

Note: tool_calls[].function.arguments is a JSON string—parse it before use.

## Configure Clients

1) Helper constructors

- Ollama: create_ollama_client(model="llama3.2", temperature=0.7, ...)
- Gemini: create_gemini_client(api_key="...", model="gemini-1.5-flash", ...)

2) From environment

```python
from faciliter_lib import create_client_from_env
client = create_client_from_env("ollama")  # "gemini" | "openai" | "mistral"
```

See docs/ENV_VARIABLES.md for full lists.

## Common Patterns

### Structured Output (JSON)

```python
from pydantic import BaseModel

class Weather(BaseModel):
    location: str
    temperature: float

res = gemini.chat("Weather in Paris?", structured_output=Weather)
if res["structured"]:
    data = res["content"]  # Parsed JSON (dict/list), not a Pydantic instance
```

Provider support: Gemini ✅, OpenAI ✅, Mistral ❌ (no JSON schema), Ollama ❌.

### Tool Calling (OpenAI style)

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
    }
}]

out = openai_client.chat("What's the weather in Tokyo?", tools=tools)
for tc in out["tool_calls"]:
    args = json.loads(tc["function"]["arguments"])  # parse string
```

Provider support: OpenAI ✅, Mistral ✅, Gemini (limited/tooling differs) ⚠️, Ollama ⚠️ (model dependent).

### Conversation History

```python
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
    {"role": "user", "content": "Tell me about Python"}
]
resp = client.chat(messages)
```

### System Instruction

```python
resp = openai_client.chat("Be terse.", system_message="You are a concise assistant")
```

Note: System messages are honored on OpenAI/Azure; other providers may ignore.

## Provider Notes (TL;DR)

- Ollama: local inference, no token usage numbers, tool/structured support limited.
- Gemini: strong JSON schema output; use GEMINI_API_KEY.
- OpenAI/Azure: tools + JSON schema; set OPENAI_API_KEY and optionally OPENAI_BASE_URL.
- Mistral: tools supported; set MISTRAL_API_KEY.

## Best Practices

- Use env vars for keys/config in production
- Check res["structured"] before assuming JSON
- Parse tool_calls arguments with json.loads
- Keep histories compact to fit context windows
- Not all models support all features—verify per model

# LLM Guide

End-to-end documentation for faciliter-lib's unified LLM client. Works with Gemini, OpenAI/Azure OpenAI, Mistral, and Ollama.

## Overview

- Single client API across providers
- Config via code or environment
- Optional features depending on provider: tools, structured JSON, system prompts
- Robust core: retries with jitter, rate limiting, circuit breaker, tracing hooks

## Install Provider SDKs

Install only what you need:

- google-genai (Gemini)
- openai>=1.0 (OpenAI/Azure)
- mistralai (Mistral)
- ollama (local server)
- pydantic (structured outputs)

## Create Clients

```python
from faciliter_lib import (
  create_ollama_client, create_gemini_client, create_client_from_env
)

ollama = create_ollama_client(model="llama3.2", temperature=0.7)
gemini = create_gemini_client(api_key="...", model="gemini-1.5-flash")
openai_client = create_client_from_env("openai")  # needs OPENAI_API_KEY
mistral = create_client_from_env("mistral")       # needs MISTRAL_API_KEY
```

You can also build a config and pass it to LLMClient directly (see `faciliter_lib.llm.llm_config`).

## Chat API

```python
resp = ollama.chat("Hello")
print(resp["content"])  # text

messages = [
  {"role": "user", "content": "Hi"},
  {"role": "assistant", "content": "Hello"},
  {"role": "user", "content": "Tell me a joke"},
]
resp = openai_client.chat(messages, system_message="You are witty")
```

### Response

```python
{
  "content": str | dict | list,
  "structured": bool,
  "tool_calls": [
    {"type": "function", "function": {"name": str, "arguments": str}}
  ],
  "usage": {"input_tokens": int, "output_tokens": int, "total_tokens": int, "cost_usd": float}
}
```

Note: arguments is a JSON string; parse with json.loads.

## Structured Output

Request JSON-typed outputs using a Pydantic model. The client sends the model's JSON Schema to the provider when supported.

```python
from pydantic import BaseModel

class Weather(BaseModel):
  location: str
  temperature: float

r = gemini.chat("Weather in Paris?", structured_output=Weather)
if r["structured"]:
  data = r["content"]  # parsed JSON (dict/list)
```

Provider support:
- Gemini: yes (response_schema + response_mime_type)
- OpenAI/Azure: yes (response_format=json_schema)
- Mistral: no JSON schema support at this time
- Ollama: no JSON schema support

## Tools (Function Calling)

OpenAI-style tools where supported.

```python
import json

tools = [{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "Get weather for a city",
    "parameters": {
      "type": "object",
      "properties": {"city": {"type": "string"}},
      "required": ["city"]
    }
  }
}]

out = openai_client.chat("Weather in Tokyo?", tools=tools)
for tc in out["tool_calls"]:
  args = json.loads(tc["function"]["arguments"])  # Now call your backend function
```

Support:
- OpenAI/Azure: yes
- Mistral: yes
- Gemini: differs; limited in this abstraction
- Ollama: model-dependent

## Environment Variables

See `docs/ENV_VARIABLES.md` for complete lists. Common ones:

- OPENAI_API_KEY, OPENAI_BASE_URL
- GEMINI_API_KEY
- MISTRAL_API_KEY
- OLLAMA_MODEL, OLLAMA_BASE_URL

Create from env:

```python
from faciliter_lib import create_client_from_env
client = create_client_from_env("openai")
```

## Adapters

Basic shims to interop with libraries without hard dependencies:

- LangChain-like: `LangChainChatAdapter(provider, model, ...)` with .invoke([...])
- LlamaIndex-like: `LlamaIndexCustomLLM(provider, model, ...)` with .complete(prompt)

Import from `faciliter_lib.llm.adapters`.

## Orchestrator Under the Hood

The client uses an async orchestrator:

- Retries with exponential jitter (fast path under tests)
- Per-(provider, model) rate limiting and optional global limiter
- Circuit breaker per model (failure threshold with reset)
- Concurrency control and background worker queues
- Tracing hooks via faciliter_lib.tracing

Most of this is automatic; tune at the provider layer when needed.

## Troubleshooting

- ImportError: install the provider SDK for the provider you use.
- Structured outputs not returned: ensure the provider/model supports JSON schema.
- Tool calls missing: confirm the model supports function calling and your tool schema is valid.
- Azure OpenAI: set OPENAI_BASE_URL to your Azure endpoint and use the deployment name as model.
- Ollama: make sure the model is pulled and the daemon is running.

## Examples

See `examples/example_llm_usage.py` for runnable snippets.

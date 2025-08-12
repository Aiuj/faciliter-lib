# LLM Quick Reference

## Installation

The LLM module is included in `faciliter-lib` and requires Python 3.12+.

Runtime dependencies (installed by the package):
- `google-genai` (official Google GenAI Python SDK for Gemini)
- `ollama` (official Ollama Python client)
- `pydantic` (for structured outputs)

No LangChain dependency is required for LLM calls.

## Quick Start

```python
from faciliter_lib.llm import create_ollama_client, create_gemini_client

# Local Ollama (single turn)
client = create_ollama_client(model="llama3.2", temperature=0.7)
resp = client.chat("Hello, how are you?")
print(resp["content"])  # plain text

# Google Gemini (single turn)
client = create_gemini_client(api_key="your-key", model="gemini-1.5-flash")
resp = client.chat("Explain quantum computing")
print(resp["content"])  # plain text
```

## Key Features

✅ Unified interface across providers  
✅ Environment configuration (sensible defaults, .from_env helpers)  
✅ Native tool/function-calling structures  
✅ Structured outputs with Pydantic schemas (response_schema)  
✅ Single-turn and multi-turn support  
✅ Thinking mode for Gemini 2.5 models  
✅ Optional Google Search grounding (Gemini)  
✅ Graceful error handling

## Response Format

```python
{
    "content": str | dict,    # text for normal calls, dict for structured outputs
    "structured": bool,       # True if structured_output was requested
    "tool_calls": list,       # provider-reported function calls (if any)
    "usage": dict,            # usage metadata (if available)
    "error": str | None       # present on failure
}
```

## Configuration Methods

1) Direct instantiation
```python
client = create_ollama_client(model="llama3.2", temperature=0.8)
```

2) From environment
```python
from faciliter_lib.llm import create_client_from_env
client = create_client_from_env("ollama")
```

3) Using config objects
```python
from faciliter_lib.llm import LLMClient, OllamaConfig
config = OllamaConfig(model="llama3.2", temperature=0.8)
client = LLMClient(config)
```

### Environment variables
- Common:
    - `LLM_PROVIDER` = `gemini` | `ollama`
- Gemini (Developer API):
    - `GEMINI_API_KEY` (or `GOOGLE_GENAI_API_KEY`)
    - `GEMINI_MODEL` (default: `gemini-1.5-flash`)
    - `GEMINI_TEMPERATURE` (default: `0.1`)
    - `GEMINI_MAX_TOKENS`
    - `GEMINI_THINKING_ENABLED` = `true|false`
    - `GEMINI_BASE_URL` (default: Google endpoint)
- Ollama:
    - `OLLAMA_MODEL` (default: `qwen3:1.7b`)
    - `OLLAMA_TEMPERATURE` (default: `0.1`)
    - `OLLAMA_MAX_TOKENS`
    - `OLLAMA_THINKING_ENABLED` = `true|false`
    - `OLLAMA_BASE_URL` (default: `http://localhost:11434`)
    - `OLLAMA_TIMEOUT`, `OLLAMA_NUM_CTX`, `OLLAMA_NUM_PREDICT`, `OLLAMA_REPEAT_PENALTY`, `OLLAMA_TOP_K`, `OLLAMA_TOP_P`

## Common Patterns

### Structured Output (Pydantic)
```python
from pydantic import BaseModel

class Weather(BaseModel):
        location: str
        temperature: float

# Pass the Pydantic class; providers enforce schema natively when supported
resp = client.chat("Weather in Paris?", structured_output=Weather)
# resp["content"] is a dict (Pydantic exported via model_dump)
print(resp["content"]["location"], resp["content"]["temperature"])
```

### Tool Calling (OpenAI-style functions)
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

resp = client.chat("What's the weather in Tokyo?", tools=tools)
```

### Google Search Grounding (Gemini only)
```python
from faciliter_lib.llm import create_gemini_client
client = create_gemini_client(api_key="your-key", model="gemini-1.5-flash")
resp = client.chat("What are the latest Mars mission updates?", use_search_grounding=True)
print(resp["content"])
```
Notes: This flag is forwarded to all providers. Providers that don't support grounding will ignore it.

### System message and multi-turn
```python
messages = [
    {"role": "system", "content": "You are concise and helpful."},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "Tell me about Python"}
]
resp = client.chat(messages)
```

## Provider behavior

- Gemini (google-genai):
    - Single turn: uses `models.generate_content()`
    - Multi-turn: uses `chats.create(...).send_message()`
    - Structured: passes your Pydantic class via `response_schema`; returns `dict` (from BaseModel.model_dump)
    - Thinking (2.5-series): if `thinking_enabled=True`, sets `include_thoughts`; if disabled, sets `thinking_budget=0` for non‑pro models
    - Tools: passes the provided functions list through
    - Search grounding: when `use_search_grounding=True`, enables Google Search tool and tool_config per official docs

- Ollama (ollama):
    - Uses `ollama.chat()` with OpenAI-style messages
    - Structured: uses `format='json'`; validates with Pydantic when provided; returns `dict`
    - Tools: passes functions through (model support varies)
    - Search grounding: ignored (not supported)

## Provider Comparison

| Feature | Ollama | Gemini |
|---------|--------|--------|
| Cost | Free (local) | Paid API |
| Privacy | Local | Cloud |
| Setup | Run Ollama server | API key |
| Models | Open-source | Google models |
| Tools | Model-dependent | Native support |
| Structured Output | JSON + Pydantic validate | response_schema + parsed |
| Thinking | N/A | 2.5-series (configurable) |

## Best Practices

1. Prefer environment-based configuration for deployments
2. Check `response["error"]` and handle gracefully
3. Verify model support for tools/structured output
4. Monitor usage with cloud providers
5. Keep prompts concise to stay within context

## References
- Google GenAI Python SDK: https://googleapis.github.io/python-genai/
- Gemini Structured Output: https://ai.google.dev/gemini-api/docs/structured-output
- Gemini Thinking Mode: https://ai.google.dev/gemini-api/docs/thinking
- Gemini Text Generation: https://ai.google.dev/gemini-api/docs/text-generation

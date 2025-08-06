# LLM Quick Reference

## Installation

The LLM module is included in `faciliter-lib` and requires Python 3.12+.

Dependencies:
- `langchain-google-genai` (for Gemini support)
- `langchain-ollama` (for Ollama support)
- `pydantic` (for structured outputs)

## Quick Start

```python
from faciliter_lib import create_ollama_client, create_gemini_client

# Local Ollama
client = create_ollama_client(model="llama3.2", temperature=0.7)
response = client.chat("Hello, how are you?")
print(response["content"])

# Google Gemini  
client = create_gemini_client(api_key="your-key", model="gemini-1.5-flash")
response = client.chat("Explain quantum computing")
print(response["content"])
```

## Key Features

✅ **Unified Interface**: Same API for all providers  
✅ **Environment Configuration**: Auto-configure from env vars  
✅ **Tool Support**: OpenAI-compatible function calling  
✅ **Structured Output**: Get JSON responses with Pydantic models  
✅ **Conversation History**: Multi-turn conversations  
✅ **Thinking Mode**: Step-by-step reasoning  
✅ **Error Handling**: Graceful error responses  

## Response Format

```python
{
    "content": "The LLM's response text",
    "structured": False,           # True if structured output requested
    "tool_calls": [],             # List of function calls made
    "usage": {},                  # Token usage statistics  
    "error": None                 # Error message if failed
}
```

## Configuration Methods

1. **Direct instantiation**:
   ```python
   client = create_ollama_client(model="llama3.2", temperature=0.8)
   ```

2. **Environment variables**:
   ```python
   client = create_client_from_env("ollama")
   ```

3. **Configuration objects**:
   ```python
   config = OllamaConfig(model="llama3.2", temperature=0.8)
   client = LLMClient(config)
   ```

## Common Patterns

### Structured Output
```python
from pydantic import BaseModel

class Weather(BaseModel):
    location: str
    temperature: float

response = client.chat("Weather in Paris?", structured_output=Weather)
```

### Tool Calling
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
}]

response = client.chat("What's the weather in Tokyo?", tools=tools)
```

### Conversation History
```python
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "Tell me about Python"}
]

response = client.chat(messages)
```

## Provider Comparison

| Feature | Ollama | Gemini |
|---------|--------|--------|
| **Cost** | Free (local) | Paid API |
| **Privacy** | Full privacy | Cloud-based |
| **Setup** | Requires Ollama server | Requires API key |
| **Models** | Open source models | Google's models |
| **Performance** | Depends on hardware | Consistent cloud performance |
| **Tool Calling** | Model dependent | Native support |

## Best Practices

1. **Use environment variables** for configuration in production
2. **Handle errors** by checking the `error` field in responses  
3. **Test model compatibility** - not all models support all features
4. **Monitor usage** with cloud providers to avoid unexpected costs
5. **Keep conversations short** to stay within context limits

# LLM Module Documentation

The LLM module provides a unified interface for working with different Large Language Model providers, currently supporting Google Gemini and local Ollama APIs.

## Features

- **Provider Abstraction**: Use the same interface for different LLM providers
- **Configuration Management**: Environment-based configuration with sensible defaults  
- **Tool Support**: Pass tools in OpenAI JSON format for function calling
- **Structured Output**: Get structured JSON responses using Pydantic models
- **Thinking Mode**: Enable step-by-step reasoning for supported models
- **Conversation History**: Support for multi-turn conversations
- **Grounding with Search (Gemini)**: Optional Google Search grounding for fresher, corroborated answers on supported models

## Quick Start

### Basic Usage

```python
from faciliter_lib import create_ollama_client, create_gemini_client

# Create an Ollama client
client = create_ollama_client(
    model="llama3.2",
    temperature=0.7,
    thinking_enabled=True
)

# Simple chat
response = client.chat("What is the capital of France?")
print(response["content"])
```

### Using Gemini

```python
client = create_gemini_client(
    api_key="your-api-key",
    model="gemini-1.5-flash",
    temperature=0.3
)

response = client.chat("Explain quantum computing briefly.")
print(response["content"])
```

### Environment Configuration

Set environment variables and create clients automatically:

```bash
# For Ollama
export OLLAMA_MODEL=llama3.2
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_TEMPERATURE=0.7

# For Gemini  
export GEMINI_API_KEY=your-api-key
export GEMINI_MODEL=gemini-1.5-flash
export GEMINI_TEMPERATURE=0.3
```

```python
from faciliter_lib import create_client_from_env

# Uses environment variables
client = create_client_from_env("ollama")  # or "gemini"
```

## Configuration

### Ollama Configuration

Available environment variables:

- `OLLAMA_MODEL`: Model name (default: "llama3.2")
- `OLLAMA_BASE_URL`: Server URL (default: "http://localhost:11434")  
- `OLLAMA_TEMPERATURE`: Sampling temperature (default: "0.7")
- `OLLAMA_MAX_TOKENS`: Maximum tokens to generate
- `OLLAMA_THINKING_ENABLED`: Enable thinking mode ("true"/"false")
- `OLLAMA_TIMEOUT`: Request timeout in seconds (default: "60")
- `OLLAMA_NUM_CTX`: Context window size
- `OLLAMA_NUM_PREDICT`: Max tokens to predict
- `OLLAMA_REPEAT_PENALTY`: Repetition penalty
- `OLLAMA_TOP_K`: Top-K sampling
- `OLLAMA_TOP_P`: Top-P sampling

### Gemini Configuration

Available environment variables:

- `GEMINI_API_KEY`: Google API key (required)
- `GEMINI_MODEL`: Model name (default: "gemini-1.5-flash")
- `GEMINI_BASE_URL`: API base URL (default: Google's API endpoint)
- `GEMINI_TEMPERATURE`: Sampling temperature (default: "0.7")  
- `GEMINI_MAX_TOKENS`: Maximum tokens to generate
- `GEMINI_THINKING_ENABLED`: Enable thinking mode ("true"/"false")

## Advanced Usage

### Conversation History

```python
messages = [
    {"role": "user", "content": "Hello, I'm planning a trip."},
    {"role": "assistant", "content": "Great! Where are you thinking of going?"},
    {"role": "user", "content": "I want to visit Japan. Any recommendations?"}
]

response = client.chat(
    messages, 
    system_message="You are a helpful travel assistant."
)
```

### Structured Output

```python
from pydantic import BaseModel
from typing import Optional

class WeatherResponse(BaseModel):
    location: str
    temperature: float
    condition: str
    humidity: Optional[int] = None

response = client.chat(
    "What's the weather in Paris?",
    structured_output=WeatherResponse
)

if response["structured"] and not response.get("error"):
    weather_data = response["content"]
    print(f"Temperature in {weather_data.location}: {weather_data.temperature}°C")
```

### Using Tools

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather", 
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country, e.g. 'Paris, France'"
                    },
                    "unit": {
                        "type": "string", 
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat(
    "What's the weather in Tokyo?",
    tools=tools
)

# Check for tool calls
if response["tool_calls"]:
    for tool_call in response["tool_calls"]:
        print(f"Tool: {tool_call['function']['name']}")
        print(f"Args: {tool_call['function']['arguments']}")
```

### Grounding with Search (Gemini)

Enable Google Search grounding for supported Gemini models to augment responses with up-to-date web information.

```python
client = create_gemini_client(api_key="your-api-key", model="gemini-1.5-flash")

resp = client.chat(
    "Summarize the latest news about Mars exploration.",
    use_search_grounding=True,
)
print(resp["content"])  # text response augmented by Google Search
```

Notes:
- The `use_search_grounding` flag is provider-agnostic and is forwarded to providers; only Gemini implements it currently. Other providers will ignore it unless they support a similar capability in the future.

## Response Format

All chat methods return a dictionary with the following structure:

```python
{
    "content": "The response text",
    "structured": False,  # True if structured output was requested
    "tool_calls": [],     # List of tool calls made by the model
    "usage": {},          # Usage statistics (varies by provider)
    "error": None         # Error message if something went wrong
}
```

## API Reference

### Classes

#### `LLMClient`

Main client class for interacting with LLMs.

**Methods:**
- `chat(messages, tools=None, structured_output=None, system_message=None, use_search_grounding=False)`: Send chat message
- `get_model_info()`: Get information about the current model

#### `GeminiConfig` / `OllamaConfig`

Configuration classes for each provider.

**Methods:**
- `from_env()`: Create configuration from environment variables

### Utility Functions

- `create_ollama_client(**kwargs)`: Create Ollama client with parameters
- `create_gemini_client(**kwargs)`: Create Gemini client with parameters  
- `create_client_from_env(provider)`: Create client from environment variables

## Error Handling

The library handles errors gracefully and returns them in the response:

```python
response = client.chat("Hello")

if response.get("error"):
    print(f"Error: {response['error']}")
else:
    print(f"Response: {response['content']}")
```

## Best Practices

1. **Use Environment Variables**: Store API keys and configuration in environment variables
2. **Handle Errors**: Always check for errors in responses
3. **Model Compatibility**: Not all models support tools, structured output, or search grounding
4. **Rate Limiting**: Be mindful of API rate limits, especially with cloud providers
5. **Context Management**: Keep track of conversation history for multi-turn chats

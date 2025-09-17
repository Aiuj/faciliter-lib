# LLM Module Documentation

The LLM module provides a unified interface for working with different Large Language Model providers, currently supporting Google Gemini, OpenAI, Azure OpenAI, and local Ollama APIs.

## Features

- **Provider Abstraction**: Use the same interface for different LLM providers
- **Factory-based Creation**: Simplified client creation with intelligent defaults
- **Configuration Management**: Environment-based configuration with sensible defaults  
- **Tool Support**: Pass tools in OpenAI JSON format for function calling
- **Structured Output**: Get structured JSON responses using Pydantic models
- **Thinking Mode**: Enable step-by-step reasoning for supported models
- **Conversation History**: Support for multi-turn conversations
- **Grounding with Search (Gemini)**: Optional Google Search grounding for fresher, corroborated answers on supported models

## Quick Start

### Simplest Usage (Recommended)

The new factory-based approach automatically detects your configuration and creates the appropriate client:

```python
from faciliter_lib.llm import create_llm_client

# Auto-detect provider from environment variables
client = create_llm_client()

# Simple chat
response = client.chat("What is the capital of France?")
print(response["content"])
```

### Provider-Specific Creation

```python
from faciliter_lib.llm import create_llm_client

# Use a specific provider with overrides
client = create_llm_client(
    provider="openai",
    model="gpt-4",
    temperature=0.2
)

# Or use Ollama with custom settings
client = create_llm_client(
    provider="ollama",
    model="llama3.2",
    thinking_enabled=True
)
```

### Using the Factory Class Directly

```python
from faciliter_lib.llm import LLMFactory

# Create with factory methods
client = LLMFactory.openai(model="gpt-4", temperature=0.3)
client = LLMFactory.gemini(model="gemini-1.5-pro")
client = LLMFactory.ollama(model="llama3.2")

# Or use the main factory method
client = LLMFactory.create(provider="openai", model="gpt-4")
```

### Environment Configuration

Set environment variables and let the factory handle detection:

```bash
# Option 1: Explicit provider setting
export LLM_PROVIDER=openai

# Option 2: Let the factory auto-detect based on available API keys
# For OpenAI
export OPENAI_API_KEY=sk-your-api-key
export OPENAI_MODEL=gpt-4o-mini

# For Gemini  
export GEMINI_API_KEY=your-api-key
export GEMINI_MODEL=gemini-1.5-flash

# For Ollama
export OLLAMA_MODEL=llama3.2
export OLLAMA_BASE_URL=http://localhost:11434

# For Azure OpenAI
export AZURE_OPENAI_API_KEY=your-api-key
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_DEPLOYMENT=gpt-4
```

```python
from faciliter_lib.llm import create_llm_client

# Factory auto-detects the provider and uses environment settings
client = create_llm_client()

```

## Environment Variables Reference

### Auto-Detection

The factory automatically detects the provider based on available environment variables:

1. If `LLM_PROVIDER` is set, it uses that provider explicitly
2. Otherwise, it checks for provider-specific API keys in this order:
   - `GEMINI_API_KEY` or `GOOGLE_GENAI_API_KEY` → Gemini
   - `OPENAI_API_KEY` → OpenAI  
   - `AZURE_OPENAI_API_KEY` → Azure OpenAI
   - `OLLAMA_BASE_URL` or `OLLAMA_HOST` → Ollama
   - Default fallback → Ollama

### OpenAI Configuration

Available environment variables:

- `OPENAI_API_KEY`: OpenAI API key (required)
- `OPENAI_MODEL`: Model name (default: "gpt-4o-mini")
- `OPENAI_BASE_URL`: Custom base URL for OpenAI-compatible endpoints
- `OPENAI_TEMPERATURE`: Sampling temperature (default: "0.7")
- `OPENAI_MAX_TOKENS`: Maximum tokens to generate
- `OPENAI_THINKING_ENABLED`: Enable thinking mode ("true"/"false")
- `OPENAI_ORGANIZATION`: OpenAI organization ID
- `OPENAI_PROJECT`: OpenAI project ID

### Azure OpenAI Configuration

Available environment variables:

- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key (required)
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL (required)
- `AZURE_OPENAI_API_VERSION`: API version (default: "2024-08-01-preview")
- `AZURE_OPENAI_DEPLOYMENT`: Deployment name (maps to model)
- `AZURE_OPENAI_TEMPERATURE`: Sampling temperature (default: "0.7")
- `AZURE_OPENAI_MAX_TOKENS`: Maximum tokens to generate
- `AZURE_OPENAI_THINKING_ENABLED`: Enable thinking mode ("true"/"false")

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

### Using Custom Configuration Objects

```python
from faciliter_lib.llm import LLMFactory, OpenAIConfig, GeminiConfig

# Create a custom configuration
config = OpenAIConfig(
    api_key="sk-your-key",
    model="gpt-4",
    temperature=0.3,
    max_tokens=2000,
    thinking_enabled=True
)

# Use the factory with the custom config
client = LLMFactory.from_config(config)

# Or apply overrides to environment-loaded config
client = LLMFactory.from_config(
    OpenAIConfig.from_env(),
    temperature=0.8,  # Override just the temperature
    max_tokens=1500
)
```

### Mixing Environment and Manual Configuration

```python
from faciliter_lib.llm import create_llm_client

# Load base settings from env, override specific parameters
client = create_llm_client(
    provider="openai",  # Use OpenAI even if LLM_PROVIDER is different
    model="gpt-4",      # Override the model from environment
    temperature=0.2     # Override temperature
    # API key still comes from OPENAI_API_KEY env var
)
```

### Conversation History

```python
from faciliter_lib.llm import create_llm_client

client = create_llm_client()

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
from faciliter_lib.llm import create_llm_client

class WeatherResponse(BaseModel):
    location: str
    temperature: float
    condition: str
    humidity: Optional[int] = None

client = create_llm_client(provider="openai")  # Structured output works well with OpenAI

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
from faciliter_lib.llm import create_llm_client

client = create_llm_client()

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

```

Notes:

- The `use_search_grounding` flag is provider-agnostic and is forwarded to providers; only Gemini implements it currently. Other providers will ignore it unless they support a similar capability in the future.

## Factory Class Methods

The `LLMFactory` class provides multiple creation methods:

### Factory.create()

Main factory method that intelligently creates clients based on parameters:

```python
from faciliter_lib.llm import LLMFactory

# Auto-detect from environment
client = LLMFactory.create()

# Specify provider with overrides
client = LLMFactory.create(provider="openai", model="gpt-4", temperature=0.3)

# Use with existing config
config = OpenAIConfig(api_key="sk-...", model="gpt-4")
client = LLMFactory.create(config=config)
```

### Provider-Specific Methods

```python
# Direct provider methods
client = LLMFactory.openai(model="gpt-4", temperature=0.2)
client = LLMFactory.gemini(api_key="key", model="gemini-1.5-pro")
client = LLMFactory.ollama(model="llama3.2", base_url="http://localhost:11434")
client = LLMFactory.azure_openai(deployment="gpt-4", azure_endpoint="https://...")
client = LLMFactory.openai_compatible(base_url="http://localhost:8000")
```

### Convenience Functions

For simpler usage, several convenience functions are available:

```python
from faciliter_lib.llm import create_llm_client, create_client_from_env

# Main convenience function - recommended for most use cases
client = create_llm_client()  # Auto-detect
client = create_llm_client(provider="openai", model="gpt-4")

# Environment-based creation
client = create_client_from_env()  # Auto-detect provider
client = create_client_from_env(provider="gemini")
```

## Migration from utils.py

If you were using the old `utils.py` functions, here's how to migrate:

```python
# Old way
from faciliter_lib.llm.utils import create_gemini_client
client = create_gemini_client(model="gemini-pro")

# New way (all approaches work)
from faciliter_lib.llm import LLMFactory, create_llm_client

# Option 1: Use the factory
client = LLMFactory.gemini(model="gemini-pro")

# Option 2: Use the main convenience function
client = create_llm_client(provider="gemini", model="gemini-pro")

# Option 3: Backward-compatible functions still work
from faciliter_lib.llm import create_gemini_client
client = create_gemini_client(model="gemini-pro")
```

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

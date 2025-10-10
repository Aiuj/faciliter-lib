# LLM Environment Variables

This file lists all environment variables that can be used to configure the LLM clients.

## Embeddings Configuration

### Unified Configuration (Recommended for Single Provider)

Simplest approach when using one embedding provider:

```bash
export EMBEDDING_PROVIDER=infinity              # Provider: openai|google_genai|ollama|infinity|local
export EMBEDDING_MODEL=BAAI/bge-small-en-v1.5  # Model name
export EMBEDDING_BASE_URL=http://localhost:7997 # Server URL (works for all providers)
export EMBEDDING_TIMEOUT=30                     # Request timeout in seconds
export EMBEDDING_DIMENSION=384                  # Optional: embedding dimension
export EMBEDDING_TASK_TYPE=SEMANTIC_SIMILARITY  # Optional: task type
```

### Provider-Specific Configuration (For Multi-Provider Setups)

When running multiple embedding providers simultaneously:

```bash
# Common defaults
export EMBEDDING_BASE_URL=http://default-server:7997
export EMBEDDING_TIMEOUT=30

# Provider-specific overrides (take precedence)
export INFINITY_BASE_URL=http://infinity-server:7997
export INFINITY_TIMEOUT=30
export OLLAMA_URL=http://ollama-server:11434
export OLLAMA_TIMEOUT=60
export OPENAI_BASE_URL=https://api.openai.com/v1

# API keys
export OPENAI_API_KEY=your-key
export GOOGLE_GENAI_API_KEY=your-key
```

**Priority Chain:**
- Ollama: `OLLAMA_URL` > `EMBEDDING_BASE_URL` > default
- Infinity: `EMBEDDING_BASE_URL` > default
- OpenAI: `OPENAI_BASE_URL` > `EMBEDDING_BASE_URL` > default

**See:** [EMBEDDING_URL_CONFIGURATION.md](../docs/EMBEDDING_URL_CONFIGURATION.md) for detailed configuration guide

## Ollama Configuration

```bash
# Model and basic settings
export OLLAMA_MODEL=llama3.2                    # Model name to use

# For LLM (chat/generation)
export OLLAMA_BASE_URL=http://localhost:11434   # Ollama server URL for LLM
export OLLAMA_TEMPERATURE=0.7                   # Sampling temperature (0.0-2.0)
export OLLAMA_MAX_TOKENS=                       # Maximum tokens to generate (optional)
export OLLAMA_THINKING_ENABLED=false            # Enable step-by-step thinking mode

# For Embeddings (use unified config or provider-specific)
export EMBEDDING_BASE_URL=http://localhost:11434  # Recommended: unified config
# OR
# export OLLAMA_URL=http://localhost:11434       # Alternative: provider-specific

# Timeout settings
export EMBEDDING_TIMEOUT=30                     # Unified timeout for embeddings
# OR  
# export OLLAMA_TIMEOUT=60                      # Provider-specific timeout
export OLLAMA_TIMEOUT=60                        # Timeout for LLM operations

# Advanced Ollama settings
export OLLAMA_NUM_CTX=                          # Context window size (optional)
export OLLAMA_NUM_PREDICT=                      # Max tokens to predict (optional)
export OLLAMA_REPEAT_PENALTY=                   # Repetition penalty (optional)
export OLLAMA_TOP_K=                            # Top-K sampling (optional)
export OLLAMA_TOP_P=                            # Top-P sampling (optional)
```

## Example .env file

```bash
# Required settings
export GEMINI_API_KEY=your-google-api-key       # Google API key (REQUIRED)

# Model and basic settings  
export GEMINI_MODEL=gemini-1.5-flash            # Model name to use
export GEMINI_TEMPERATURE=0.7                   # Sampling temperature (0.0-2.0)
export GEMINI_MAX_TOKENS=                       # Maximum tokens to generate (optional)
export GEMINI_THINKING_ENABLED=false            # Enable step-by-step thinking mode

# Advanced Gemini settings
export GEMINI_BASE_URL=https://generativelanguage.googleapis.com  # API base URL
```

## Example .env file

```bash
# Choose your provider
# For Ollama (local)
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.7
OLLAMA_THINKING_ENABLED=true

# For Gemini (cloud)
# GEMINI_API_KEY=your-actual-api-key-here
# GEMINI_MODEL=gemini-1.5-flash
# GEMINI_TEMPERATURE=0.3
```

## Usage in Code

```python
from faciliter_lib import create_client_from_env

# Will use environment variables automatically
ollama_client = create_client_from_env("ollama")
gemini_client = create_client_from_env("gemini")
```

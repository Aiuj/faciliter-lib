# LLM Environment Variables

This file lists all environment variables that can be used to configure the LLM clients.

## Ollama Configuration

```bash
# Model and basic settings
export OLLAMA_MODEL=llama3.2                    # Model name to use
export OLLAMA_BASE_URL=http://localhost:11434   # Ollama server URL  
export OLLAMA_TEMPERATURE=0.7                   # Sampling temperature (0.0-2.0)
export OLLAMA_MAX_TOKENS=                       # Maximum tokens to generate (optional)
export OLLAMA_THINKING_ENABLED=false            # Enable step-by-step thinking mode

# Advanced Ollama settings
export OLLAMA_TIMEOUT=60                        # Request timeout in seconds
export OLLAMA_NUM_CTX=                          # Context window size (optional)
export OLLAMA_NUM_PREDICT=                      # Max tokens to predict (optional)
export OLLAMA_REPEAT_PENALTY=                   # Repetition penalty (optional)
export OLLAMA_TOP_K=                            # Top-K sampling (optional)
export OLLAMA_TOP_P=                            # Top-P sampling (optional)
```

## Gemini Configuration

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

## OpenAI / Azure OpenAI Configuration

```bash
# Standard OpenAI
export OPENAI_API_KEY=your-openai-key           # Required for OpenAI
export OPENAI_MODEL=gpt-4o-mini                 # Default model
export OPENAI_TEMPERATURE=0.7                   # Optional
export OPENAI_MAX_TOKENS=                       # Optional

# Azure OpenAI (use OpenAI client with custom base URL)
export OPENAI_BASE_URL=https://<resource>.openai.azure.com/openai/deployments/<deployment>/chat/completions?api-version=<version>
# Use your deployment name as the model
```

## Mistral Configuration

```bash
export MISTRAL_API_KEY=your-mistral-key         # Required
export MISTRAL_MODEL=mistral-small              # Default model
export MISTRAL_TEMPERATURE=0.7                  # Optional
export MISTRAL_MAX_TOKENS=                      # Optional
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

# For OpenAI
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini

# For Azure OpenAI
# OPENAI_API_KEY=...
# OPENAI_BASE_URL=https://<resource>.openai.azure.com/openai/deployments/<deployment>/chat/completions?api-version=2024-02-01
# OPENAI_MODEL=<deployment>

# For Mistral
# MISTRAL_API_KEY=...
# MISTRAL_MODEL=mistral-small
```

## Usage in Code

```python
from faciliter_lib import create_client_from_env

# Will use environment variables automatically
ollama_client = create_client_from_env("ollama")
gemini_client = create_client_from_env("gemini")
```

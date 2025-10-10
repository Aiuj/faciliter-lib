# Embedding URL Configuration Guide

This guide explains how to configure embedding server URLs in `faciliter-lib`, supporting both simple single-provider setups and advanced multi-provider scenarios.

## Quick Start (Single Provider)

For most use cases where you're using one embedding provider, use the unified configuration:

```bash
# Common configuration (works for all providers)
EMBEDDING_PROVIDER=infinity  # or openai, ollama, google_genai, local
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_BASE_URL=http://localhost:7997
EMBEDDING_TIMEOUT=30
EMBEDDING_DIMENSION=384
```

This is the **recommended** approach for simplicity and consistency.

## How It Works

### Fallback Priority Chain

Each provider follows a specific priority chain for URL and timeout configuration:

#### Ollama Provider
1. Explicit `base_url` parameter to constructor
2. `OLLAMA_URL` environment variable
3. `EMBEDDING_BASE_URL` environment variable (common default)
4. Default: `http://localhost:11434`

**Timeout:**
1. Explicit `timeout` parameter
2. `OLLAMA_TIMEOUT`
3. `EMBEDDING_TIMEOUT`
4. `None` (no timeout)

#### Infinity Provider
1. Explicit `base_url` parameter to constructor
3. `INFINITY_BASE_URL` environment variable
4. `EMBEDDING_BASE_URL` environment variable (common default)
5. Default: `http://localhost:7997`

**Timeout:**
1. Explicit `timeout` parameter
2. `INFINITY_TIMEOUT`
3. `EMBEDDING_TIMEOUT`
4. `OLLAMA_TIMEOUT` (legacy fallback)
5. Default: `30` seconds

#### OpenAI Provider
1. Explicit `base_url` parameter to constructor
2. `OPENAI_BASE_URL` environment variable
3. `BASE_URL` environment variable
4. `EMBEDDING_BASE_URL` environment variable (common default)
5. `None` (uses OpenAI default API endpoint)

## Configuration Examples

### Example 1: Simple Single Provider (Recommended)

Using Infinity as your only embedding provider:

```bash
# .env file
EMBEDDING_PROVIDER=infinity
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_BASE_URL=http://localhost:7997
EMBEDDING_TIMEOUT=30
```

```python
from faciliter_lib.embeddings import create_embedding_client

# Automatically uses EMBEDDING_BASE_URL
client = create_embedding_client()
embedding = client.generate_embedding("Hello, world!")
```

### Example 2: Multi-Provider Setup with Redundancy

Running multiple embedding services for redundancy or A/B testing:

```bash
# .env file
EMBEDDING_BASE_URL=http://localhost:7997  # Default for all providers

# Provider-specific overrides for multi-provider scenarios
INFINITY_BASE_URL=http://infinity-server:7997
OLLAMA_URL=http://ollama-server:11434
OPENAI_BASE_URL=https://api.openai.com/v1

# Provider-specific timeouts
INFINITY_TIMEOUT=30
OLLAMA_TIMEOUT=60
EMBEDDING_TIMEOUT=45  # Default for any provider without specific timeout
```

```python
from faciliter_lib.embeddings import (
    create_infinity_client,
    create_ollama_client,
    create_openai_client
)

# Each client uses its provider-specific URL
infinity_client = create_infinity_client()  # Uses INFINITY_BASE_URL
ollama_client = create_ollama_client()      # Uses OLLAMA_URL
openai_client = create_openai_client()      # Uses OPENAI_BASE_URL

# Fallback strategy
def get_embedding_with_fallback(text: str):
    providers = [infinity_client, ollama_client, openai_client]
    for client in providers:
        try:
            return client.generate_embedding(text)
        except Exception as e:
            print(f"Provider {client.__class__.__name__} failed: {e}")
            continue
    raise Exception("All embedding providers failed")
```

### Example 3: Development vs Production

Different configurations for different environments:

**Development (.env.dev):**
```bash
EMBEDDING_PROVIDER=ollama
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_TIMEOUT=60
```

**Production (.env.prod):**
```bash
# Primary provider
EMBEDDING_PROVIDER=infinity
EMBEDDING_BASE_URL=http://infinity-prod:7997
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_TIMEOUT=30

# Backup providers for redundancy
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-...
OLLAMA_URL=http://ollama-backup:11434
```

### Example 4: Explicit Parameter Override

Override configuration programmatically:

```python
from faciliter_lib.embeddings import create_infinity_client

# Override environment variables with explicit parameters
client = create_infinity_client(
    base_url="http://custom-server:8080",  # Overrides all env vars
    timeout=120,                            # Custom timeout
    model="custom/model"
)
```

### Example 5: Testing Multiple Models

Test different models on different servers:

```bash
# .env.test
EMBEDDING_BASE_URL=http://localhost:7997  # Default

# Test server URLs
INFINITY_BASE_URL=http://localhost:7997    # bge-small
OLLAMA_URL=http://localhost:7998      # different Infinity with bge-large
```

```python
# Compare model performance
small_client = create_infinity_client(
    base_url="http://localhost:7997",
    model="BAAI/bge-small-en-v1.5"
)

large_client = create_infinity_client(
    base_url="http://localhost:7998",
    model="BAAI/bge-large-en-v1.5"
)

# Benchmark
text = "Test embedding performance"
small_emb = small_client.generate_embedding(text)
large_emb = large_client.generate_embedding(text)

print(f"Small model time: {small_client.get_embedding_time_ms()}ms")
print(f"Large model time: {large_client.get_embedding_time_ms()}ms")
```

## Best Practices

### ✅ DO

1. **Use `EMBEDDING_BASE_URL` for single-provider setups**
   ```bash
   EMBEDDING_BASE_URL=http://localhost:7997
   EMBEDDING_TIMEOUT=30
   ```

2. **Use provider-specific URLs for multi-provider scenarios**
   ```bash
   INFINITY_BASE_URL=http://infinity:7997
   OLLAMA_URL=http://ollama:11434
   OPENAI_BASE_URL=https://api.openai.com/v1
   ```

3. **Set EMBEDDING_TIMEOUT as a common default**
   ```bash
   EMBEDDING_TIMEOUT=45  # Default for all
   INFINITY_TIMEOUT=30   # Override for Infinity
   ```

4. **Document your configuration strategy in your project README**

### ❌ DON'T

1. **Don't mix approaches unnecessarily**
   ```bash
   # Confusing: which one is used?
   EMBEDDING_BASE_URL=http://localhost:7997
   INFINITY_BASE_URL=http://different-server:7997
   ```

2. **Don't forget provider-specific URLs take precedence**
   ```bash
   # OLLAMA_URL will be used, not EMBEDDING_BASE_URL
   EMBEDDING_BASE_URL=http://localhost:7997
   OLLAMA_URL=http://localhost:11434
   ```

## Troubleshooting

### Issue: Client using wrong URL

**Symptoms:** Connection errors, timeouts

**Debug:**
```python
from faciliter_lib.embeddings import embeddings_settings

print(f"Infinity URL: {embeddings_settings.infinity_url}")
print(f"Ollama URL: {embeddings_settings.ollama_url}")
print(f"OpenAI Base URL: {embeddings_settings.base_url}")
```

**Solution:** Check environment variable priority chain above

### Issue: Provider-specific URL not being used

**Problem:** Set `INFINITY_BASE_URL` but still using `EMBEDDING_BASE_URL`

**Solution:** Ensure environment variables are loaded before importing:
```python
# Load .env BEFORE importing
from dotenv import load_dotenv
load_dotenv()

# Now import
from faciliter_lib.embeddings import create_infinity_client
```

## Environment Variable Reference

| Variable | Provider | Priority | Default | Description |
|----------|----------|----------|---------|-------------|
| `EMBEDDING_BASE_URL` | All | Low | None | Common default URL for all providers |
| `EMBEDDING_TIMEOUT` | All | Low | None | Common default timeout in seconds |
| `OLLAMA_URL` | Ollama | High | `localhost:11434` | Ollama-specific URL |
| `OLLAMA_TIMEOUT` | Ollama | High | None | Ollama-specific timeout |
| `INFINITY_BASE_URL` | Infinity | High | `localhost:7997` | Infinity-specific URL |
| `INFINITY_TIMEOUT` | Infinity | High | 30 | Infinity-specific timeout |
| `OPENAI_BASE_URL` | OpenAI | High | None | OpenAI/compatible endpoint |
| `BASE_URL` | OpenAI | Medium | None | Alternative OpenAI URL var |

**Priority:** High = checked first, Low = checked last (fallback)

## Summary

- 🎯 **Simple use case:** Use `EMBEDDING_BASE_URL` + `EMBEDDING_TIMEOUT`
- 🔄 **Multi-provider:** Use provider-specific URLs (OLLAMA_URL, INFINITY_BASE_URL, etc.)
- ✨ **Backward compatible:** All existing configurations continue to work
- 🚀 **Flexible:** Mix and match as needed for your use case
- 📝 **Documented:** Clear priority chains for troubleshooting

For more examples, see:
- [EMBEDDINGS_QUICK_REFERENCE.md](./EMBEDDINGS_QUICK_REFERENCE.md)
- [INFINITY_QUICKSTART.md](./INFINITY_QUICKSTART.md)
- [INFINITY_PROVIDER.md](./INFINITY_PROVIDER.md)

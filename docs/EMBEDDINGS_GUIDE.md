# Embeddings Comprehensive Guide

Complete guide to using embeddings in `faciliter-lib` with production patterns, high availability, authentication, and advanced configuration.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Production Setup](#production-setup)
  - [Single Host](#single-host-simple)
  - [High Availability](#high-availability-recommended)
  - [Authentication](#authentication)
- [Configuration Reference](#configuration-reference)
  - [Environment Variables](#environment-variables)
  - [URL Configuration](#url-configuration)
  - [Token Authentication](#token-authentication)
- [Automatic Fallback](#automatic-fallback)
- [Provider Details](#provider-details)
- [Advanced Patterns](#advanced-patterns)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)

## Overview

The `faciliter-lib` embeddings module provides a unified interface for generating text embeddings across multiple providers with automatic failover, authentication, and production-ready features.

### Key Features

✅ **Automatic High Availability**: Comma-separated URLs trigger automatic fallback  
✅ **Smart Health Caching**: Remembers which providers are healthy to avoid retries  
✅ **Token Authentication**: Secure your embedding servers  
✅ **Multiple Providers**: Infinity, OpenAI, Google GenAI, Local, Ollama  
✅ **Zero-Config Fallback**: `create_embedding_client()` auto-detects HA setup  
✅ **Unified Interface**: Same API across all providers  
✅ **Production Ready**: Health checks, monitoring, retry logic, graceful degradation  

## Quick Start

### Simple Single Host

```python
from faciliter_lib.embeddings import create_embedding_client

# Automatically configured from environment
client = create_embedding_client()
embedding = client.generate_embedding("Hello, world!")
```

```bash
# .env
EMBEDDING_PROVIDER=infinity
EMBEDDING_BASE_URL=http://localhost:7997
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

### High Availability (Recommended for Production)

```python
from faciliter_lib.embeddings import create_embedding_client

# Automatically creates FallbackEmbeddingClient from comma-separated URLs
client = create_embedding_client()
embedding = client.generate_embedding("Production text with auto-failover")
```

```bash
# .env - Automatic HA with comma-separated URLs
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://infinity1:7997,http://infinity2:7997,http://infinity3:7997
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

**That's it!** The library automatically detects comma-separated URLs and enables fallback.

## Production Setup

### Single Host (Simple)

For development or non-critical deployments:

```bash
EMBEDDING_PROVIDER=infinity
EMBEDDING_BASE_URL=http://localhost:7997
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384
EMBEDDING_TIMEOUT=30
EMBEDDING_CACHE_DURATION_SECONDS=7200
```

```python
from faciliter_lib.embeddings import create_embedding_client

client = create_embedding_client()
```

### High Availability (Recommended)

For production deployments requiring zero downtime:

#### Option 1: Provider-Specific URLs (Recommended)

```bash
# Multiple Infinity hosts with automatic failover
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://infinity-prod-1:7997,http://infinity-prod-2:7997,http://infinity-prod-3:7997
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DIMENSION=1024
EMBEDDING_TIMEOUT=30
EMBEDDING_CACHE_DURATION_SECONDS=7200
```

#### Option 2: Generic EMBEDDING_BASE_URL

```bash
# Works with any provider
EMBEDDING_PROVIDER=infinity
EMBEDDING_BASE_URL=http://host1:7997,http://host2:7997,http://host3:7997
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

#### Automatic Fallback Detection

```python
from faciliter_lib.embeddings import create_embedding_client

# Automatically uses FallbackEmbeddingClient when comma-separated URLs detected
client = create_embedding_client()

# Transparent failover - if host1 fails, automatically tries host2, then host3
embedding = client.generate_embedding("Production text")

# Check which provider is active
if hasattr(client, 'get_provider_stats'):
    stats = client.get_provider_stats()
    print(f"Active provider: {stats['current_provider']}/{stats['total_providers']}")
```

### Authentication

Secure your embedding servers with token-based authentication:

#### Single Token for All Hosts

```bash
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://host1:7997,http://host2:7997,http://host3:7997
INFINITY_TOKEN=shared-secret-token
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

#### Per-Host Tokens

```bash
# Each host has its own token (matched by position)
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://host1:7997,http://host2:7997,http://host3:7997
INFINITY_TOKEN=token-for-host1,token-for-host2,token-for-host3
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

```python
from faciliter_lib.embeddings import create_embedding_client

# Tokens automatically included in requests
client = create_embedding_client()
embedding = client.generate_embedding("Authenticated request")
```

#### Generic Token Fallback

```bash
# Generic token works with any provider
EMBEDDING_PROVIDER=infinity
EMBEDDING_BASE_URL=http://host1:7997,http://host2:7997
EMBEDDING_TOKEN=generic-token-1,generic-token-2
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

## Configuration Reference

### Environment Variables

#### Core Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `EMBEDDING_PROVIDER` | Provider type | `infinity`, `openai`, `ollama` |
| `EMBEDDING_MODEL` | Model name | `BAAI/bge-small-en-v1.5` |
| `EMBEDDING_DIMENSION` | Target embedding size | `384`, `768`, `1024` |
| `EMBEDDING_TIMEOUT` | Request timeout (seconds) | `30` |
| `EMBEDDING_CACHE_DURATION_SECONDS` | Cache TTL | `7200` (2 hours), `0` (disabled) |

#### URL Configuration

| Variable | Provider | Priority | Description |
|----------|----------|----------|-------------|
| `EMBEDDING_BASE_URL` | All | Low | Generic URL(s) for any provider |
| `INFINITY_BASE_URL` | Infinity | High | Infinity-specific URL(s) |
| `OLLAMA_URL` | Ollama | High | Ollama-specific URL(s) |
| `OPENAI_BASE_URL` | OpenAI | High | OpenAI/Azure endpoint(s) |

**Priority**: Provider-specific → Generic

**Multiple URLs**: Comma-separated triggers automatic fallback

#### Authentication

| Variable | Provider | Description |
|----------|----------|-------------|
| `INFINITY_TOKEN` | Infinity | Bearer token(s) for Infinity servers |
| `EMBEDDING_TOKEN` | All | Generic token(s) for any provider |
| `OPENAI_API_KEY` | OpenAI | OpenAI API key(s) |

**Token Matching**: Tokens matched to URLs by position (index)

#### Provider-Specific

**Infinity:**
```bash
INFINITY_BASE_URL=http://localhost:7997  # Single or comma-separated
INFINITY_TOKEN=optional-token            # Single or comma-separated
INFINITY_TIMEOUT=30                      # Override global timeout
```

**OpenAI:**
```bash
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
OPENAI_ORGANIZATION=org-id                  # Optional
OPENAI_PROJECT=project-id                   # Optional
```

**Google GenAI:**
```bash
GOOGLE_GENAI_API_KEY=key  # or GEMINI_API_KEY
EMBEDDING_TASK_TYPE=SEMANTIC_SIMILARITY  # Task-specific embeddings
```

**Ollama:**
```bash
OLLAMA_URL=http://localhost:11434  # Single or comma-separated
OLLAMA_TIMEOUT=60
```

**Local (HuggingFace):**
```bash
EMBEDDING_DEVICE=cuda              # cpu|cuda|auto
EMBEDDING_CACHE_DIR=/path/to/cache
EMBEDDING_TRUST_REMOTE_CODE=false
```

### URL Configuration

#### Single Provider

```bash
# Simple setup - single URL
EMBEDDING_PROVIDER=infinity
EMBEDDING_BASE_URL=http://localhost:7997
```

#### Multiple Providers (Manual Fallback)

```python
from faciliter_lib.embeddings import FallbackEmbeddingClient

# Explicit mixed provider setup
client = FallbackEmbeddingClient.from_config([
    {"provider": "infinity", "base_url": "http://localhost:7997"},
    {"provider": "ollama", "base_url": "http://localhost:11434"},
    {"provider": "openai", "api_key": "sk-..."},
], common_model="BAAI/bge-small-en-v1.5")
```

#### URL Priority Chain

Each provider checks URLs in this order:

**Infinity:**
1. Explicit `base_url` parameter
2. `INFINITY_BASE_URL` environment variable
3. `EMBEDDING_BASE_URL` environment variable
4. Default: `http://localhost:7997`

**Ollama:**
1. Explicit `base_url` parameter
2. `OLLAMA_URL` environment variable
3. `EMBEDDING_BASE_URL` environment variable
4. Default: `http://localhost:11434`

**OpenAI:**
1. Explicit `base_url` parameter
2. `OPENAI_BASE_URL` environment variable
3. `BASE_URL` environment variable
4. `EMBEDDING_BASE_URL` environment variable
5. Default: OpenAI API endpoint

### Token Authentication

#### How It Works

**Infinity** uses Bearer token authentication:

```http
POST /embeddings HTTP/1.1
Host: infinity-server:7997
Content-Type: application/json
Authorization: Bearer your-secret-token

{"model": "BAAI/bge-small-en-v1.5", "input": ["text to embed"]}
```

#### Token Matching Rules

**Equal tokens and URLs:**
```bash
INFINITY_BASE_URL=http://h1:7997,http://h2:7997,http://h3:7997
INFINITY_TOKEN=token1,token2,token3
# h1 uses token1, h2 uses token2, h3 uses token3
```

**Single token, multiple URLs:**
```bash
INFINITY_BASE_URL=http://h1:7997,http://h2:7997,http://h3:7997
INFINITY_TOKEN=shared-token
# All hosts use shared-token
```

**Fewer tokens than URLs:**
```bash
INFINITY_BASE_URL=http://h1:7997,http://h2:7997,http://h3:7997,http://h4:7997
INFINITY_TOKEN=token1,token2
# h1 uses token1, h2-h4 use token2 (last token reused)
```

#### Production Best Practices

**1. Use environment variables:**
```bash
# Good - environment variables
export INFINITY_TOKEN="production-secret-token"

# Bad - hardcoded in code
token = "secret-token-123"  # DON'T DO THIS
```

**2. Rotate tokens regularly:**
```bash
# Development
INFINITY_TOKEN=dev-token-abc123

# Staging  
INFINITY_TOKEN=staging-token-def456

# Production
INFINITY_TOKEN=prod-token-ghi789
```

**3. Use secrets management:**
```bash
# AWS Secrets Manager
INFINITY_TOKEN=$(aws secretsmanager get-secret-value --secret-id infinity-prod-token --query SecretString --output text)

# Azure Key Vault
INFINITY_TOKEN=$(az keyvault secret show --vault-name my-vault --name infinity-token --query value -o tsv)

# Kubernetes Secrets (mounted as env var in pod spec)
```

**4. Mixed authentication:**
```python
from faciliter_lib.embeddings import FallbackEmbeddingClient

# Some hosts with auth, some without
client = FallbackEmbeddingClient.from_config([
    {"provider": "infinity", "base_url": "http://public:7997"},  # No token
    {"provider": "infinity", "base_url": "http://secure:7997", "token": "secret"},
    {"provider": "openai", "api_key": "sk-..."},
])
```

## Automatic Fallback

### Zero-Config High Availability with Smart Health Tracking

The library automatically detects comma-separated URLs and creates a `FallbackEmbeddingClient` with intelligent health caching:

```bash
# This configuration...
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://h1:7997,http://h2:7997,http://h3:7997
```

```python
# ...automatically creates fallback client with health caching
from faciliter_lib.embeddings import create_embedding_client

client = create_embedding_client()
# Returns FallbackEmbeddingClient with 3 providers and health tracking!
```

### How It Works

1. **Reads environment**: Checks `INFINITY_BASE_URL`, `EMBEDDING_BASE_URL`, etc.
2. **Detects commas**: If URL contains `,` → comma-separated list
3. **Creates appropriate client**:
   - Single URL → Regular provider client
   - Multiple URLs → `FallbackEmbeddingClient` with health caching

### Smart Health Caching

The fallback client uses the cache (if available) to track provider health status:

**Benefits:**
- **Faster failover**: Skips known-unhealthy providers without retrying
- **Persistent memory**: Remembers healthy provider across requests
- **Automatic recovery**: Periodically rechecks failed providers
- **Overload detection**: Distinguishes temporary overload from permanent failures
- **No infinite loops**: Guaranteed to try each provider only once per request

**How it works:**
```python
from faciliter_lib.embeddings import FallbackEmbeddingClient

client = FallbackEmbeddingClient.from_config([
    {"provider": "infinity", "base_url": "http://h1:7997"},
    {"provider": "infinity", "base_url": "http://h2:7997"},
    {"provider": "infinity", "base_url": "http://h3:7997"},
],
    use_health_cache=True,      # Enable health caching (default)
    health_check_interval=60,   # Recheck failed providers after 60s
)

# First request: h1 fails, h2 succeeds
# -> h2 marked as healthy in cache
embedding1 = client.generate_embedding("text 1")

# Second request: goes directly to h2 (cached as healthy)
# -> h1 not retried (within health_check_interval)
embedding2 = client.generate_embedding("text 2")

# Check health status
stats = client.get_provider_stats()
print(f"Preferred provider: {stats.get('preferred_provider')}")
for provider in stats['providers']:
    print(f"Provider {provider['index']}: cached_healthy={provider['cached_healthy']}")
```

### Overload Detection and Recovery

The fallback client intelligently handles temporary server overload separately from permanent failures:

**Overload Indicators:**
- HTTP 503 (Service Unavailable)
- HTTP 429 (Too Many Requests)
- Timeout errors
- Connection pool exhausted

**Automatic Recovery:**
- **Temporary overload**: 30-second TTL, frequent rechecks
- **Permanent failure**: 60-second TTL, less frequent rechecks
- Primary server automatically becomes preferred again when it recovers
- Avoids hammering overloaded servers with constant retries

**Example:**
```python
from faciliter_lib.embeddings import FallbackEmbeddingClient

client = FallbackEmbeddingClient.from_config([
    {"provider": "infinity", "base_url": "http://primary:7997"},
    {"provider": "infinity", "base_url": "http://secondary:7997"},
],
    use_health_cache=True,
    health_check_interval=60,  # Failed providers rechecked after 60s
)

# Request 1: Primary overloaded (503) → falls back to secondary
result1 = client.generate_embedding("text 1")

# Requests 2-N: Use secondary while primary is overloaded
# (primary marked with 30s TTL, rechecked more frequently)
result2 = client.generate_embedding("text 2")

# After 30s: Primary recovers → automatically becomes preferred again
# (shorter TTL enables faster recovery to preferred provider)
import time
time.sleep(31)
result3 = client.generate_embedding("text 3")  # Back to primary

# Check provider status
stats = client.get_provider_stats()
for provider in stats['providers']:
    print(f"Provider {provider['index']}:")
    print(f"  Overloads: {provider['overloads']}")
    print(f"  Failures: {provider['failures']}")
    print(f"  Cached overloaded: {provider['cached_overloaded']}")
    print(f"  Cached healthy: {provider['cached_healthy']}")
```

**Status Tracking:**
- `overloads`: Count of temporary overload events (503, 429, timeouts)
- `failures`: Count of permanent failures (500, 404, connection errors)
- `cached_overloaded`: Provider currently marked as temporarily overloaded
- `cached_healthy`: Provider currently marked as healthy

**TTL Configuration:**
- Healthy provider: 300 seconds (5 minutes)
- Overloaded provider: 30 seconds (fast recovery)
- Failed provider: 60 seconds (moderate recovery)

### Explicit Fallback Control

```python
from faciliter_lib.embeddings import FallbackEmbeddingClient

# Explicit configuration with full control
client = FallbackEmbeddingClient.from_config([
    {"provider": "infinity", "base_url": "http://primary:7997"},
    {"provider": "infinity", "base_url": "http://backup:7997"},
],
    common_model="BAAI/bge-small-en-v1.5",
    max_retries_per_provider=2,     # Try each provider twice
    fail_on_all_providers=True,     # Raise exception if all fail
    use_health_cache=True,          # Enable health caching
    health_check_interval=60,       # Recheck interval for failed providers
)
```

### Fallback Behavior

**Health-based provider selection:**
- Uses cached preferred provider first (last known healthy)
- Skips recently-failed providers (within health_check_interval)
- Automatically rechecks failed providers periodically
- Prevents infinite retry loops

**Provider preference:**
- Successfully used providers are cached
- Next request uses cached healthy provider directly
- Failure resets preference, tries next provider

**Retry logic:**
- Configurable retries per provider
- Exponential backoff between retries
- Each provider tried maximum once per request (prevents loops)

**Failure handling:**
- `fail_on_all_providers=True`: Raises `EmbeddingGenerationError`
- `fail_on_all_providers=False`: Returns `None` (graceful degradation)
- Clear error messages listing all failed providers

**Without cache:**
- Health caching disabled if cache unavailable
- Falls back to standard round-robin failover
- All functionality still works, just without optimization

## Provider Details

### Infinity (Recommended for Production)

**Why Infinity:**
- ✅ Local deployment (privacy, no API costs)
- ✅ High throughput (GPU acceleration)
- ✅ OpenAI-compatible API
- ✅ Any HuggingFace embedding model
- ✅ Production-ready

**Setup:**

```bash
# Docker
docker run -p 7997:7997 michaelf34/infinity:latest --model-name-or-path BAAI/bge-small-en-v1.5

# Or pip
uv pip install infinity-emb[all]
infinity_emb v2 --model-name-or-path BAAI/bge-small-en-v1.5
```

**Configuration:**

```bash
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://localhost:7997
INFINITY_TOKEN=optional-auth-token
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSION=384
```

**Popular models:**
- `BAAI/bge-small-en-v1.5` (384 dims, fast, good quality)
- `BAAI/bge-base-en-v1.5` (768 dims, balanced)
- `BAAI/bge-large-en-v1.5` (1024 dims, best quality)
- `intfloat/e5-base-v2` (768 dims, multilingual)

### OpenAI

**Features:**
- Custom dimensions (reduce token costs)
- Azure OpenAI support
- Latest embedding models

**Configuration:**

```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=512  # Optional, reduce from 1536
```

**Models:**
- `text-embedding-3-small` (1536 dims, cost-effective)
- `text-embedding-3-large` (3072 dims, best performance)
- `text-embedding-ada-002` (1536 dims, legacy)

### Google GenAI

**Features:**
- Task-specific embeddings
- Grounding context support

**Configuration:**

```bash
EMBEDDING_PROVIDER=google_genai
GOOGLE_GENAI_API_KEY=your-key
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_TASK_TYPE=SEMANTIC_SIMILARITY
```

**Task types:**
- `SEMANTIC_SIMILARITY`: General similarity search
- `CLASSIFICATION`: Text classification
- `CLUSTERING`: Grouping similar texts
- `RETRIEVAL_DOCUMENT`: Document indexing
- `RETRIEVAL_QUERY`: Search queries

### Ollama (Local Experimentation)

**Configuration:**

```bash
EMBEDDING_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
```

### Local (Offline/Privacy)

**Configuration:**

```bash
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cuda  # or cpu, auto
```

## Advanced Patterns

### Pattern 1: Multi-Region HA

```bash
# Geographic distribution
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://us-east:7997,http://eu-west:7997,http://ap-south:7997
INFINITY_TOKEN=region-token-us,region-token-eu,region-token-ap
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

### Pattern 2: Local with Cloud Backup

```python
from faciliter_lib.embeddings import FallbackEmbeddingClient

# Try local first, fall back to cloud
client = FallbackEmbeddingClient.from_config([
    {"provider": "infinity", "base_url": "http://localhost:7997"},
    {"provider": "ollama", "base_url": "http://localhost:11434"},
    {"provider": "openai", "api_key": "sk-..."},
], common_model="BAAI/bge-small-en-v1.5")
```

### Pattern 3: Docker Compose Stack

```yaml
# docker-compose.yml
services:
  infinity-primary:
    image: michaelf34/infinity:latest
    command: --model-name-or-path BAAI/bge-small-en-v1.5
    ports:
      - "7997:7997"
  
  infinity-backup:
    image: michaelf34/infinity:latest
    command: --model-name-or-path BAAI/bge-small-en-v1.5
    ports:
      - "7998:7997"
  
  app:
    environment:
      EMBEDDING_PROVIDER: infinity
      INFINITY_BASE_URL: http://infinity-primary:7997,http://infinity-backup:7997
      EMBEDDING_MODEL: BAAI/bge-small-en-v1.5
```

### Pattern 4: Per-Environment Configuration

```bash
# .env.development
EMBEDDING_PROVIDER=infinity
EMBEDDING_BASE_URL=http://localhost:7997
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# .env.staging
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://staging-h1:7997,http://staging-h2:7997
INFINITY_TOKEN=staging-shared-secret
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# .env.production
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://prod-h1:7997,http://prod-h2:7997,http://prod-h3:7997
INFINITY_TOKEN=prod-token-1,prod-token-2,prod-token-3
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DIMENSION=1024
```

### Pattern 5: Graceful Degradation

```python
from faciliter_lib.embeddings import FallbackEmbeddingClient

# Don't raise exceptions, return None instead
client = FallbackEmbeddingClient.from_config(
    provider_configs=[...],
    fail_on_all_providers=False,  # Returns None on total failure
)

embedding = client.generate_embedding("text")
if embedding is None:
    logger.warning("All embedding providers failed, using cached embedding")
    embedding = get_cached_embedding("text")
```

## Monitoring & Troubleshooting

### Health Checks

```python
# Check if provider is accessible
if client.health_check():
    print("✓ Provider is healthy")
else:
    print("✗ Provider is unhealthy")
```

### Provider Statistics (Fallback Client)

```python
if hasattr(client, 'get_provider_stats'):
    stats = client.get_provider_stats()
    print(f"Total providers: {stats['total_providers']}")
    print(f"Current provider: {stats['current_provider']}")
    print(f"Failure counts: {stats['provider_failures']}")
    
    for provider in stats['providers']:
        print(f"  Provider {provider['index']}: {provider['type']}")
        print(f"    Failures: {provider['failures']}")
```

### Performance Monitoring

```python
# Get timing information
embedding = client.generate_embedding("test")
time_ms = client.get_embedding_time_ms()
print(f"Generation took {time_ms:.2f}ms")
```

### Logging

```python
import logging

# Enable debug logging for embeddings
logging.getLogger('faciliter_lib.embeddings').setLevel(logging.DEBUG)

# Fallback-specific logging
logging.getLogger('faciliter_lib.embeddings.fallback_client').setLevel(logging.INFO)
```

### Common Issues

#### Authentication Failures (401)

```python
# Check if token is configured
from faciliter_lib.embeddings import embeddings_settings
print(f"Token configured: {bool(embeddings_settings.infinity_token)}")

# Verify token in client
if hasattr(client, 'token'):
    print(f"Client token: {client.token[:10]}...")  # First 10 chars only
```

**Fix**: Ensure environment variables are loaded before importing:

```python
from dotenv import load_dotenv
load_dotenv()  # Load .env BEFORE importing

from faciliter_lib.embeddings import create_embedding_client
client = create_embedding_client()
```

#### All Providers Failing

```python
from faciliter_lib.embeddings import EmbeddingGenerationError

try:
    embedding = client.generate_embedding("text")
except EmbeddingGenerationError as e:
    logger.error(f"All providers failed: {e}")
    
    # Check individual provider health
    if hasattr(client, 'providers'):
        for i, provider in enumerate(client.providers):
            try:
                health = provider.health_check()
                logger.info(f"Provider {i}: {'healthy' if health else 'unhealthy'}")
            except Exception as ex:
                logger.error(f"Provider {i} health check failed: {ex}")
```

#### Wrong URL Being Used

```python
# Debug URL configuration
from faciliter_lib.embeddings import embeddings_settings

print(f"Infinity URL: {embeddings_settings.infinity_url}")
print(f"Ollama URL: {embeddings_settings.ollama_url}")
print(f"Generic URL: {embeddings_settings.base_url}")
```

#### Token Not Applied

```python
# Verify token is being used
client = create_embedding_client()

if hasattr(client, 'providers'):  # Fallback client
    for i, provider in enumerate(client.providers):
        if hasattr(provider, 'token'):
            print(f"Provider {i} token: {provider.token[:10]}...")
elif hasattr(client, 'token'):  # Single client
    print(f"Client token: {client.token[:10]}...")
```

## Best Practices Summary

### For Development

```bash
# Simple single host
EMBEDDING_PROVIDER=infinity
EMBEDDING_BASE_URL=http://localhost:7997
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

### For Production

```bash
# High availability with authentication
EMBEDDING_PROVIDER=infinity
INFINITY_BASE_URL=http://h1:7997,http://h2:7997,http://h3:7997
INFINITY_TOKEN=token1,token2,token3
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DIMENSION=1024
EMBEDDING_TIMEOUT=30
EMBEDDING_CACHE_DURATION_SECONDS=7200
```

### Key Recommendations

1. **Use Infinity for production** (local, fast, privacy-friendly)
2. **Always use comma-separated URLs for HA** (automatic fallback)
3. **Secure with tokens** (per-host or shared)
4. **Enable caching** (reduce redundant calls)
5. **Monitor provider health** (track failures)
6. **Use provider-specific URLs** (clearer than generic)
7. **Batch requests** (better performance)
8. **Set appropriate timeouts** (prevent hanging)

## Related Documentation

- [EMBEDDINGS_QUICK_REFERENCE.md](./EMBEDDINGS_QUICK_REFERENCE.md) - Quick start and API reference
- [INFINITY_PROVIDER.md](./INFINITY_PROVIDER.md) - Infinity-specific details
- [INFINITY_QUICKSTART.md](./INFINITY_QUICKSTART.md) - Infinity setup guide

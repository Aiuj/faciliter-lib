# Infinity Embedding Provider

The Infinity embedding provider enables high-throughput, low-latency embedding generation using a local Infinity server.

## Overview

Infinity is a REST API server for serving embeddings with an OpenAI-compatible interface. It supports multiple embedding models and provides excellent performance for local deployment.

- **GitHub**: https://github.com/michaelfeil/infinity
- **Default Port**: 7997
- **API Format**: OpenAI-compatible

## Installation

### 1. Install Infinity Server

```bash
# Using uv (recommended)
uv pip install infinity-emb[all]

# Using Docker (recommended for production)
docker run -p 7997:7997 michaelf34/infinity:latest
```

### 2. Client Requirements

The Infinity provider in core-lib only requires `requests`:

```bash
# Install with uv
uv pip install requests

# Or add to your project dependencies
uv add requests
```

## Configuration

### Environment Variables

```bash
# Provider selection
EMBEDDING_PROVIDER=infinity

# Model selection
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# URL Configuration (choose one approach):
# Option 1: Unified configuration (recommended for single provider)
EMBEDDING_BASE_URL=http://localhost:7997
EMBEDDING_TIMEOUT=30

# Option 2: Provider-specific (for multi-provider setups)
# INFINITY_BASE_URL=http://localhost:7997
# INFINITY_TIMEOUT=30

# Optional: embedding dimension
EMBEDDING_DIMENSION=384
```

**Configuration Guide:** The library supports both unified (`EMBEDDING_BASE_URL`) and provider-specific (`INFINITY_BASE_URL`) configuration. 
- Use `EMBEDDING_BASE_URL` for simpler single-provider setups
- Use `INFINITY_BASE_URL` when running multiple embedding providers (Infinity + Ollama + OpenAI)
- See [EMBEDDINGS_GUIDE.md](./EMBEDDINGS_GUIDE.md) for complete configuration details

### Supported Models

Infinity supports any HuggingFace embedding model. Popular choices:

- `BAAI/bge-small-en-v1.5` - Fast, 384 dimensions
- `BAAI/bge-base-en-v1.5` - Balanced, 768 dimensions
- `BAAI/bge-large-en-v1.5` - High quality, 1024 dimensions
- `sentence-transformers/all-MiniLM-L6-v2` - Fast, 384 dimensions
- `intfloat/e5-small-v2` - Fast, 384 dimensions
- `intfloat/e5-base-v2` - Balanced, 768 dimensions

## Usage

### Auto-Detection from Environment

```python
from core_lib.embeddings import create_embedding_client

# Set EMBEDDING_PROVIDER=infinity in your environment
client = create_embedding_client()
embedding = client.generate_embedding("Hello, world!")
```

### Explicit Configuration

```python
from core_lib.embeddings import create_infinity_client

# Create client with defaults
client = create_infinity_client()

# Custom configuration
client = create_infinity_client(
    model="BAAI/bge-small-en-v1.5",
    base_url="http://localhost:7997",
    embedding_dim=384,
    use_l2_norm=True,
    timeout=30
)

# Generate embeddings
embedding = client.generate_embedding("Hello, world!")
print(f"Embedding dimension: {len(embedding)}")

# Batch processing
texts = ["Hello", "World", "Embedding", "Test"]
embeddings = client.generate_embedding(texts)
print(f"Generated {len(embeddings)} embeddings")
```

### Using Factory

```python
from core_lib.embeddings import EmbeddingFactory

client = EmbeddingFactory.infinity(
    model="sentence-transformers/all-MiniLM-L6-v2",
    base_url="http://localhost:7997"
)

embedding = client.generate_embedding("Test")
```

## Running Infinity Server

### Option 1: Docker (Recommended)

```bash
# Start Infinity server with a specific model
docker run -d \
  --name infinity \
  -p 7997:7997 \
  michaelf34/infinity:latest \
  --model-name-or-path BAAI/bge-small-en-v1.5

# Multiple models
docker run -d \
  --name infinity \
  -p 7997:7997 \
  michaelf34/infinity:latest \
  --model-name-or-path BAAI/bge-small-en-v1.5 \
  --model-name-or-path intfloat/e5-base-v2
```

### Option 2: Python Package with uv

```bash
# Install with uv
uv pip install infinity-emb[all]

# Run server using uv
uv run infinity_emb \
  --model-name-or-path BAAI/bge-small-en-v1.5 \
  --port 7997

# With GPU support
uv run infinity_emb \
  --model-name-or-path BAAI/bge-small-en-v1.5 \
  --device cuda \
  --port 7997
```

## Health Check

```python
client = create_infinity_client()

# Check if server is healthy
if client.health_check():
    print("Infinity server is healthy")
else:
    print("Infinity server is not responding")
```

## Available Models

```python
client = create_infinity_client()

# Get list of available models on the server
models = client.get_available_models()
print(f"Available models: {models}")

# Get info about current model
info = client.get_model_info()
print(f"Model info: {info}")
```

## Performance Tips

1. **Batch Processing**: Always batch multiple texts together for better throughput
   ```python
   # Good - batch processing
   embeddings = client.generate_embedding(["text1", "text2", "text3", ...])
   
   # Less efficient - individual calls
   for text in texts:
       embedding = client.generate_embedding(text)
   ```

2. **Enable Caching**: Embeddings are automatically cached based on text and model
   ```python
   # Subsequent calls with same text return cached results
   embedding1 = client.generate_embedding("Hello")  # Generates
   embedding2 = client.generate_embedding("Hello")  # From cache
   ```

3. **Use Appropriate Model**: Choose model based on your needs
   - Small models (384 dim): Fastest, good for most tasks
   - Base models (768 dim): Balanced performance/quality
   - Large models (1024+ dim): Best quality, slower

4. **GPU Acceleration**: Run Infinity with GPU for significant speedup
   ```bash
   uv run infinity_emb --model-name-or-path BAAI/bge-base-en-v1.5 --device cuda
   ```

## Error Handling

```python
from core_lib.embeddings import create_infinity_client, EmbeddingGenerationError

client = create_infinity_client()

try:
    embedding = client.generate_embedding("Test text")
except EmbeddingGenerationError as e:
    print(f"Embedding generation failed: {e}")
    # Handle error (retry, fallback, etc.)
```

## Comparison with Other Providers

| Provider | Speed | Cost | Setup | Best For |
|----------|-------|------|-------|----------|
| Infinity | Very Fast | Free | Medium | High-throughput local deployment |
| Ollama | Fast | Free | Easy | Local development, single model |
| OpenAI | Fast | Paid | Easy | Production, no infrastructure |
| Local | Slow | Free | Hard | Custom models, full control |

## Integration with mcp-doc-qa

To use Infinity with mcp-doc-qa, simply set the environment variables in `.env`:

```bash
EMBEDDING_PROVIDER=infinity
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_BASE_URL=http://localhost:7997
EMBEDDING_TIMEOUT=30
EMBEDDING_DIMENSION=384
```

The system will automatically detect and use the Infinity provider without any code changes.

## Troubleshooting

### Connection Refused

```
Error: Failed to connect to Infinity server at http://localhost:7997
```

**Solution**: Ensure Infinity server is running
```bash
# Check if server is running
curl http://localhost:7997/health

# Start server if not running
docker run -d -p 7997:7997 michaelf34/infinity:latest --model-name-or-path BAAI/bge-small-en-v1.5
```

### Model Not Found

```
Error: Infinity server returned HTTP error: 404
```

**Solution**: Model not loaded on server. Restart with correct model:
```bash
docker restart infinity
# or specify model explicitly
docker run -d -p 7997:7997 michaelf34/infinity:latest --model-name-or-path YOUR_MODEL_NAME
```

### Timeout Errors

```
Error: Infinity request timed out after 30s
```

**Solution**: Increase timeout or use GPU acceleration:
```python
client = create_infinity_client(timeout=60)
```

## Advanced Usage

### Custom Infinity Configuration

```python
from core_lib.embeddings.infinity_provider import InfinityEmbeddingClient

client = InfinityEmbeddingClient(
    model="BAAI/bge-large-en-v1.5",
    base_url="http://custom-host:7997",
    embedding_dim=1024,
    use_l2_norm=True,
    timeout=60
)
```

### Using with Different Ports

```python
# Infinity on non-standard port
client = create_infinity_client(base_url="http://localhost:8080")
```

### Multiple Infinity Servers

```python
# Server 1: Small fast model
client_fast = create_infinity_client(
    model="BAAI/bge-small-en-v1.5",
    base_url="http://localhost:7997"
)

# Server 2: Large quality model
client_quality = create_infinity_client(
    model="BAAI/bge-large-en-v1.5",
    base_url="http://localhost:7998"
)
```

## References

- [Infinity GitHub](https://github.com/michaelfeil/infinity)
- [Infinity Documentation](https://github.com/michaelfeil/infinity/blob/main/docs/README.md)
- [HuggingFace Embedding Models](https://huggingface.co/models?pipeline_tag=sentence-similarity&sort=trending)
- [core-lib Embeddings Documentation](./EMBEDDINGS_QUICK_REFERENCE.md)

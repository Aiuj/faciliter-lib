# Embeddings Quick Reference

## Installation

The Embeddings module is included in `faciliter-lib` and requires Python 3.12+.

Optional dependencies for different providers:
- `openai` (for OpenAI embeddings)
- `google-genai` (for Google GenAI embeddings with task types)
- `sentence-transformers` (for local HuggingFace models)
- `transformers` + `torch` (alternative for local models)
- `ollama` (for local Ollama embeddings)
- `requests` (for Infinity server embeddings)

## Quick Start

```python
from faciliter_lib.embeddings import create_embedding_client

# Auto-detect from environment
client = create_embedding_client()
embedding = client.generate_embedding("Hello world")
embeddings = client.generate_embedding(["Text 1", "Text 2"])

# Provider-specific
from faciliter_lib.embeddings import create_openai_client, create_google_genai_client

# OpenAI embeddings
client = create_openai_client(model="text-embedding-3-small")
embedding = client.generate_embedding("Your text here")

# Google GenAI with task types
from faciliter_lib.embeddings import TaskType
client = create_google_genai_client(
    model="text-embedding-004",
    task_type=TaskType.SEMANTIC_SIMILARITY
)
```

## Key Features

✅ Unified interface across all providers  
✅ Multiple providers: OpenAI, Google GenAI, Local (HuggingFace), Ollama, Infinity  
✅ Task type support (SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING, etc.)  
✅ Environment configuration with auto-detection  
✅ Local model inference (privacy-friendly)  
✅ High-throughput local server (Infinity)  
✅ Custom embedding dimensions (where supported)  
✅ L2 normalization support  
✅ Batch processing for efficiency  
✅ Health checks and performance monitoring

## Supported Providers

### OpenAI

- **Models**: `text-embedding-3-small`, `text-embedding-3-large`, `text-embedding-ada-002`
- **Features**: Custom dimensions, Azure OpenAI support
- **API Key**: `OPENAI_API_KEY`

### Google GenAI

- **Models**: `text-embedding-004` and others
- **Features**: Task types, grounding context, title parameter
- **API Key**: `GOOGLE_GENAI_API_KEY` or `GEMINI_API_KEY`

### Infinity (NEW)

- **Models**: Any HuggingFace embedding model
- **Features**: High-throughput local server, OpenAI-compatible API, GPU support
- **Setup**: Requires Infinity server running (Docker or pip)
- **Popular**: `BAAI/bge-small-en-v1.5`, `BAAI/bge-base-en-v1.5`, `intfloat/e5-base-v2`
- **Documentation**: See [INFINITY_PROVIDER.md](./INFINITY_PROVIDER.md)

### Local (HuggingFace)

- **Models**: Any sentence-transformers or transformers model
- **Features**: No API calls, GPU/CPU support, model caching
- **Popular**: `sentence-transformers/all-MiniLM-L6-v2`, `BAAI/bge-base-en-v1.5`

### Ollama

- **Models**: Local Ollama embedding models
- **Features**: Local inference, model management via Ollama
- **Setup**: Requires local Ollama installation

## Task Types

```python
from faciliter_lib.embeddings import TaskType

TaskType.SEMANTIC_SIMILARITY    # Default for similarity search
TaskType.CLASSIFICATION         # For text classification tasks  
TaskType.CLUSTERING            # For grouping similar texts
TaskType.RETRIEVAL_DOCUMENT    # For indexing documents (official Google GenAI)
TaskType.RETRIEVAL_QUERY       # For search queries (official Google GenAI)
TaskType.CODE_RETRIEVAL_QUERY  # For code search queries
TaskType.QUESTION_ANSWERING    # For Q&A systems
TaskType.FACT_VERIFICATION     # For fact-checking applications
```

## Configuration Methods

### 1. Direct Creation

```python
from faciliter_lib.embeddings import create_openai_client, create_google_genai_client

# OpenAI with custom settings
client = create_openai_client(
    model="text-embedding-3-small",
    embedding_dim=512,  # Custom dimensions
    api_key="your-key"
)

# Google GenAI with task type
client = create_google_genai_client(
    model="text-embedding-004",
    task_type="SEMANTIC_SIMILARITY",
    title="Document Similarity Search"
)
```

### 2. Factory Pattern

```python
from faciliter_lib.embeddings import EmbeddingFactory

# Auto-detect from environment
client = EmbeddingFactory.create()

# Explicit provider
client = EmbeddingFactory.create(
    provider="openai",
    model="text-embedding-3-large"
)

# Provider-specific methods
client = EmbeddingFactory.openai(model="text-embedding-3-small")
client = EmbeddingFactory.google_genai(task_type="CLASSIFICATION")
client = EmbeddingFactory.local(model="sentence-transformers/all-MiniLM-L6-v2")
```

### 3. From Environment

```python
from faciliter_lib.embeddings import create_client_from_env

# Uses environment variables for configuration
client = create_client_from_env()
```

### 4. Configuration Objects

```python
from faciliter_lib.embeddings import EmbeddingsConfig, EmbeddingFactory

config = EmbeddingsConfig(
    provider="openai",
    model="text-embedding-3-small",
    api_key="your-key",
    task_type="SEMANTIC_SIMILARITY"
)
client = EmbeddingFactory.from_config(config)
```

## Environment Variables

### Provider Selection

```bash
EMBEDDING_PROVIDER=openai|google_genai|ollama|local
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
EMBEDDING_TASK_TYPE=SEMANTIC_SIMILARITY
EMBEDDING_TITLE="My Embedding Task"
```

### OpenAI Configuration

```bash
OPENAI_API_KEY=your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1  # For Azure or custom endpoints
OPENAI_ORGANIZATION=org-id
OPENAI_PROJECT=project-id
```

### Google GenAI Configuration
```bash
GOOGLE_GENAI_API_KEY=your-google-key
GEMINI_API_KEY=your-google-key  # Alternative
```

### Local Model Configuration
```bash
EMBEDDING_DEVICE=cpu|cuda|auto
EMBEDDING_CACHE_DIR=/path/to/model/cache
EMBEDDING_TRUST_REMOTE_CODE=true|false
EMBEDDING_USE_SENTENCE_TRANSFORMERS=true|false
```

### Ollama Configuration
```bash
OLLAMA_HOST=localhost:11434
OLLAMA_URL=http://localhost:11434
OLLAMA_TIMEOUT=30
```

## Usage Patterns

### Basic Embedding Generation
```python
from faciliter_lib.embeddings import create_embedding_client

client = create_embedding_client()

# Single text
embedding = client.generate_embedding("Your text here")
print(f"Embedding dimension: {len(embedding)}")

# Batch processing
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = client.generate_embedding(texts)
print(f"Generated {len(embeddings)} embeddings")
```

### Task-Specific Embeddings
```python
from faciliter_lib.embeddings import create_google_genai_client, TaskType

# For similarity search
similarity_client = create_google_genai_client(
    task_type=TaskType.SEMANTIC_SIMILARITY
)

# For classification
classification_client = create_google_genai_client(
    task_type=TaskType.CLASSIFICATION,
    title="Sentiment Analysis"
)

# For clustering
clustering_client = create_google_genai_client(
    task_type=TaskType.CLUSTERING
)
```

### Local Model Usage
```python
from faciliter_lib.embeddings import create_local_client

# CPU inference
client = create_local_client(
    model="sentence-transformers/all-MiniLM-L6-v2",
    device="cpu"
)

# GPU inference (if available)
gpu_client = create_local_client(
    model="BAAI/bge-large-en-v1.5",
    device="cuda"
)

# Get model information
info = client.get_model_info()
print(f"Model: {info['model_name']}, Device: {info['device']}")
```

### Normalization and Dimensions
```python
from faciliter_lib.embeddings import create_openai_client

# With L2 normalization (default)
client = create_openai_client(use_l2_norm=True)

# Without normalization
client = create_openai_client(use_l2_norm=False)

# Custom dimensions (for supported models)
client = create_openai_client(
    model="text-embedding-3-small",
    embedding_dim=512  # Reduce from default 1536
)
```

## Health Checks and Monitoring

```python
# Check if provider is accessible
if client.health_check():
    print("Provider is healthy")

# Get timing information
embedding = client.generate_embedding("test")
time_ms = client.get_embedding_time_ms()
print(f"Generation took {time_ms:.2f}ms")

# Provider-specific information
if hasattr(client, 'get_model_info'):
    info = client.get_model_info()
    print(f"Model info: {info}")
```

## Error Handling

```python
from faciliter_lib.embeddings import EmbeddingGenerationError

try:
    client = create_embedding_client(provider="openai")
    embedding = client.generate_embedding("Your text")
except ImportError as e:
    print(f"Missing dependency: {e}")
    # Install required package: pip install openai
except EmbeddingGenerationError as e:
    print(f"Embedding generation failed: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## Provider Comparison

| Provider | Local | API Key | Custom Dims | Task Types | Batch |
|----------|-------|---------|-------------|------------|-------|
| OpenAI | ❌ | ✅ | ✅ | ❌ | ✅ |
| Google GenAI | ❌ | ✅ | ❌ | ✅ | ✅ |
| Local (HF) | ✅ | ❌ | ❌ | ❌ | ✅ |
| Ollama | ✅ | ❌ | ❌ | ❌ | ✅ |

## Best Practices

1. **Provider Selection**:
   - Use OpenAI for production with custom dimensions
   - Use Google GenAI for task-specific embeddings
   - Use Local models for privacy or offline usage
   - Use Ollama for local experimentation

2. **Performance**:
   - Batch multiple texts together for efficiency
   - Enable L2 normalization for similarity tasks
   - Use GPU for local models when available

3. **Configuration**:
   - Set environment variables for easy switching
   - Use task types for specialized use cases
   - Cache local models to avoid redownloading

4. **Error Handling**:
   - Always wrap embedding calls in try-catch
   - Check health status before heavy usage
   - Have fallback providers configured

## Migration from Legacy

If migrating from the old singleton pattern:

```python
# Old way
from faciliter_lib.embeddings import get_embedding_client
client = get_embedding_client()  # Still works!

# New recommended way
from faciliter_lib.embeddings import create_embedding_client
client = create_embedding_client()  # Enhanced auto-detection
```

The legacy API remains fully compatible while the new API provides enhanced capabilities and multiple provider support.
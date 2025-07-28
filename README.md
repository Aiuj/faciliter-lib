# 🧰 faciliter-lib

`faciliter-lib` is a shared Python library for internal MCP agent tools. It provides reusable utilities, AI model access logic, and base classes used across multiple microservices in the `mcp-tools` ecosystem.

---

## 📦 Features

- Reusable utility functions
- Redis-based caching system with configurable TTL
- MCP (Model Context Protocol) utilities
- Shared data classes and model access logic
- Easy integration in monorepo and external tools
- Fully tested with Pytest
- Type hints support

---

## 🔧 Installation

### From GitHub (recommended for external tools)

```bash
pip install git+https://github.com/Aiuj/faciliter-lib.git@v0.2.0
```

### Using uv

```bash
uv add git+https://github.com/Aiuj/faciliter-lib.git@v0.2.0
```

### For local development

```bash
# Clone the repository
git clone https://github.com/Aiuj/faciliter-lib.git
cd faciliter-lib

# Install in editable mode
pip install -e ../faciliter-lib
# OR with uv
uv pip install -e ../faciliter-lib
```

And add in the `.vscode/settings.json` the following:

```json
{
    "python.analysis.autoImportCompletions": true,
    "python.analysis.includeUserSymbols": true,
    "python.analysis.userFileIndexingLimit": -1,
    "python.analysis.extraPaths": [
        "../faciliter-lib"
    ]
}
```

### In requirements.txt

```txt
git+https://github.com/Aiuj/faciliter-lib.git@v0.2.0#egg=faciliter-lib
```

---

## 🚀 Usage

### Cache Manager

```python
from faciliter_lib import RedisCache, set_cache, cache_get, cache_set

# Initialize the singleton cache (must be called before cache_get/cache_set)
set_cache(ttl=3600)  # name and other params are optional

# Using the singleton cache
result = cache_get({"query": "some data"})
if result is None:
    result = expensive_operation()
    cache_set({"query": "some data"}, result, ttl=3600)

# Using direct cache instance (advanced usage)
cache = RedisCache("my_app")
cache.connect()
cached_result = cache.get(input_data)
if cached_result is None:
    result = compute_result(input_data)
    cache.set(input_data, result, ttl=7200)
```

#### Cache API

- `set_cache(name="faciliter", config=None, ttl=None, time_out=None)`:  
  Initializes the global cache singleton. Call this before using `cache_get` or `cache_set`.  
  - `name`: Cache namespace (default: "faciliter")
  - `config`: Optional `RedisConfig` instance
  - `ttl`: Default time-to-live for cache entries (seconds)
  - `time_out`: Redis connection timeout (seconds)

- `cache_get(input_data)`:  
  Returns cached output for the given input, or `None` if not found.

- `cache_set(input_data, output_data, ttl=None)`:  
  Stores output for the given input in the cache. Optional `ttl` overrides the default.

- `RedisCache(name, config=None, ttl=None, time_out=None)`:  
  Direct cache instance for advanced use.  
  - `.connect()`: Connects to Redis
  - `.get(input_data)`: Gets cached value
  - `.set(input_data, output_data, ttl=None)`: Sets cached value

### MCP Utils

```python
from faciliter_lib import parse_from, get_transport_from_args

# Parse JSON from string or dict
data = parse_from('{"key": "value"}')  # Returns dict

# Get transport from command line args
transport = get_transport_from_args()  # Returns 'stdio', 'sse', etc.
```

#### MCP Utils API

- `parse_from(obj)`:  
  Parses a JSON string or returns the object if already a dict/list.

- `get_transport_from_args()`:  
  Detects the transport type from command-line arguments (e.g., 'stdio', 'sse').

---

## ⚙️ Configuration

The Redis cache can be configured using environment variables:

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PREFIX=cache_my_app:
export REDIS_CACHE_TTL=3600
export REDIS_PASSWORD=your_password  # Optional
export REDIS_TIMEOUT=4
```

---

## 🧪 Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=faciliter_lib

# Format code
black faciliter_lib tests

# Lint code
flake8 faciliter_lib tests
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

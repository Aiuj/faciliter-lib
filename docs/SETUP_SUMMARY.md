# core-lib Setup and Installation Guide

## 🚀 Installation Methods

### For External Applications

```bash
# Using pip
pip install git+https://github.com/Aiuj/core-lib.git@v0.3.0

# Using uv  
uv add git+https://github.com/Aiuj/core-lib.git@v0.3.0

# In requirements.txt
git+https://github.com/Aiuj/core-lib.git@v0.3.0#egg=core-lib
```

### For Local Development

```bash
# Clone and install in editable mode
git clone https://github.com/Aiuj/core-lib.git
cd core-lib
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## 📦 Usage Examples

### Basic Cache Usage

```python
from core_lib import cache_get, cache_set

# Simple caching
input_data = {"query": "expensive_computation", "params": [1, 2, 3]}
result = cache_get(input_data, name="my_app")

if result is None:
    # Cache miss - compute result
    result = expensive_function(input_data)
    cache_set(input_data, result, ttl=3600, name="my_app")

print(result)
```

### Advanced Cache Usage

```python
from core_lib import RedisCache
from core_lib.cache import RedisConfig

# Custom configuration
config = RedisConfig(
    host="localhost",
    port=6379,
    db=1,
    prefix="myapp:",
    ttl=7200,
    password="optional_password"
)

# Create cache instance
cache = RedisCache("my_service", config=config)
cache.connect()

if cache.connected:
    cached_data = cache.get({"user_id": 123})
    if cached_data is None:
        fresh_data = fetch_user_data(123)
        cache.set({"user_id": 123}, fresh_data, ttl=1800)
```

### MCP Utilities

```python
from core_lib import get_transport_from_args
from core_lib.tracing import parse_from

# Parse JSON strings or dicts (now in tracing module)
data = parse_from('{"key": "value"}')  # Returns dict

# Get transport from command line
transport = get_transport_from_args()  # Returns 'stdio', 'sse', etc.
```

## 🔧 Configuration

Set these environment variables for Redis configuration:

```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PREFIX=cache:
export REDIS_CACHE_TTL=3600
export REDIS_PASSWORD=your_password  # Optional
export REDIS_TIMEOUT=4
```

## 🧪 Testing & Development

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=core_lib

# Format code
uv run black core_lib tests

# Lint code  
uv run flake8 core_lib tests
```

## 📋 Build Distribution Packages

```bash
# Install build tools
uv run pip install build

# Build source and wheel distributions
uv run python -m build

# Files will be created in dist/
# - core_lib-0.3.0.tar.gz (source)
# - core_lib-0.3.0-py3-none-any.whl (wheel)
```

## 🎯 Next Steps for Production

1. **Set up CI/CD pipeline** for automated testing and releases
2. **Configure Redis** in your production environment 
3. **Version tagging** - create git tags for releases (e.g., `v0.2.0`)
4. **Documentation** - consider adding Sphinx docs if the library grows
5. **Type checking** - add mypy for static type checking

## 🔍 Verification Commands

```bash
# Test import
uv run python -c "import core_lib; print(f'v{getattr(core_lib, '__version__', 'unknown')}')"

# Test individual imports  
uv run python -c "from core_lib import RedisCache, cache_get, parse_from; print('OK')"

# Run example
uv run python examples/example_usage.py
```

The library is now properly configured and ready for distribution! 🎉

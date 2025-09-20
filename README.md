# 🧰 faciliter-lib

`faciliter-lib` is a shared Python library for internal MCP agent tools. It provides reusable utilities, AI model access logic, and base classes used across multiple microservices in the `mcp-tools` ecosystem.

---

## 📦 Features

- Reusable utility functions
- Redis-based caching system with configurable TTL
- MCP (Model Context Protocol) utilities
- LLM client with support for multiple providers (OpenAI, Gemini, Ollama)
- Excel file processing and markdown conversion
- Document categorization system
- Language detection utilities
- Shared data classes and model access logic
- Easy integration in monorepo and external tools
- Fully tested with Pytest
- Type hints support

---

## 🔧 Installation

### From GitHub (recommended for external tools)

```bash
pip install git+https://github.com/Aiuj/faciliter-lib.git@v0.2.3
```

### Using uv

```bash
uv add git+https://github.com/Aiuj/faciliter-lib.git@v0.2.3
```

### For local development

```bash
# Clone the repository
git clone https://github.com/Aiuj/faciliter-lib.git
cd faciliter-lib

# Install in editable mode
pip install -e .
# OR with uv
uv pip install -e .
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

### In pyproject.toml

```txt
"faciliter-lib @ git+https://github.com/Aiuj/faciliter-lib.git",
```

### In requirements.txt

```txt
git+https://github.com/Aiuj/faciliter-lib.git@v0.2.3#egg=faciliter-lib
```

---

## Library updates

To tag a new version, after commiting:

```bash
git tag -a 0.x.y -m "Release version 0.x.y"
git push origin 0.x.y
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

### Excel Manager

Process Excel files and convert them to markdown format:

```python
from faciliter_lib import ExcelManager

# Initialize with Excel file path
excel_manager = ExcelManager("data.xlsx")

# Load the workbook
workbook = excel_manager.load()

# Convert all sheets to individual markdown tables (NEW API)
sheet_markdowns = excel_manager.to_markdown()

# Each item in the list has sheet info and markdown
for sheet_data in sheet_markdowns:
    print(f"Sheet: {sheet_data['sheet_name']}")
    print(f"Language: {sheet_data['language']}")
    print(sheet_data['markdown'])

# Or get combined markdown with titles
combined_markdown = excel_manager.to_combined_markdown()
print(combined_markdown)

# Get structured content with metadata (alternative)
content = excel_manager.get_content(
    max_rows=100,           # Limit rows per sheet
    add_col_headers=True,   # Add A, B, C column headers
    add_row_headers=True,   # Add 1, 2, 3 row numbers
    detect_language=True    # Detect content language
)

for sheet_data in content:
    print(f"Sheet: {sheet_data['sheet_name']}")
    print(f"Language: {sheet_data['language']}")
    print(f"Rows: {len(sheet_data['rows'])}")
    print(sheet_data['markdown'])
```

#### Excel Manager API

- `ExcelManager(excel_path)`: Initialize with path to Excel file
- `.load()`: Load the workbook (required before other operations)
- `.to_markdown(max_rows=None, add_col_headers=True, add_row_headers=True, detect_language=True)`: Convert all sheets to list of individual markdown tables
- `.to_combined_markdown(...)`: Convert all sheets to single combined markdown with titles
- `.get_content(...)`: Get structured data with metadata for each sheet
- `.get_sheet_tables(ws, ...)`: Extract data from a specific worksheet

### Document Categories

Access predefined document categories for FAQ and content classification:

```python
from faciliter_lib.config import DOC_CATEGORIES

# Access all categories
for category in DOC_CATEGORIES:
    print(f"{category['key']}: {category['label']}")
```

#### Categories API

- `CATEGORIES_BY_KEY`: Dictionary for fast lookup by category key

### Language Utilities

```python
from faciliter_lib import LanguageUtils

# Detect language of text
result = LanguageUtils.detect_language("Hello world")
print(result)  # {'lang': 'en', 'score': 0.168...}

language = result['lang']  # 'en'
confidence = result['score']  # 0.168...

# Other language utilities
# See docs/language_utils.md for complete API

# If you need multiple candidate languages with confidence scores, use `detect_languages`:
#
# ```python
# # Returns a list like [{'lang': 'fr', 'score': 0.99}, ...] filtered by `min_confidence`.
# candidates = LanguageUtils.detect_languages("Bonjour tout le monde!", min_confidence=0.2)
# print(candidates)  # Example: [{'lang': 'fr', 'score': 0.99}]
# ```
```

---

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

- **[Excel Manager](docs/excel_manager.md)** - Complete guide for Excel file processing
- **[Cache System](docs/cache.md)** - Redis caching configuration and usage
- **[LLM Integration](docs/llm.md)** - Multi-provider LLM client documentation
- **[Language Utils](docs/language_utils.md)** - Language detection and utilities
- **[MCP Utils](docs/mcp_utils.md)** - Model Context Protocol helpers
- **[Environment Variables](docs/ENV_VARIABLES.md)** - Configuration reference
- **[Setup Summary](docs/SETUP_SUMMARY.md)** - Development setup guide

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

```pwsh
# Install development dependencies with uv
uv pip install -e ".[dev]"

# Activate uv virtual environment (Windows PowerShell)
& .\.venv\Scripts\Activate.ps1

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

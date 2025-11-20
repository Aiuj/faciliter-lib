# 🧰 core-lib

`core-lib` is a shared Python library for internal MCP agent tools. It provides reusable utilities, AI model access logic, and base classes used across multiple microservices in the `mcp-tools` ecosystem.

---

## 📦 Features

- Reusable utility functions
- **🆕 Centralized Logging** - Unified logging with console, file, OTLP, and OVH LDP handlers
- Redis-based caching system with configurable TTL
- **🆕 Redis-based job queue system** with background worker support
- **🆕 Time-based authentication** - Secure HMAC-based auth for FastAPI/MCP servers
- **🆕 FastAPI OpenAPI utilities** - Add API key auth to Swagger UI with one function call
- MCP (Model Context Protocol) utilities
- LLM client with support for multiple providers (OpenAI, Gemini, Ollama)
- Excel file processing and markdown conversion
- Document categorization system
- Language detection utilities
- Shared data classes and model access logic
- Easy integration in monorepo and external tools
- Fully tested with Pytest
- Type hints support
- **🆕 Unified Settings Management** - Comprehensive configuration system with .env support
- **🆕 Settings Singleton Manager** - Thread-safe singleton pattern for application-wide config

---

## ⚙️ Settings Management (New!)

`core-lib` now includes a powerful, unified settings management system that handles all your application configuration:

```python
from core_lib.config import StandardSettings

# Auto-configure from environment variables and .env files
settings = StandardSettings.from_env()

print(f"App: {settings.app_name} v{settings.version}")
print(f"Environment: {settings.environment}")

# Access service configurations if enabled
if settings.llm:
    print(f"LLM: {settings.llm.provider} - {settings.llm.model}")
if settings.cache:
    print(f"Cache: {settings.cache.host}:{settings.cache.port}")
```

### Key Features:
- **Auto-detection**: Automatically enables services based on environment variables
- **Type-safe**: Full validation and type conversion
- **Backward compatible**: Works with existing config classes
- **Easy extension**: Simple to add custom settings
- **.env support**: Automatic discovery and loading
- **Multi-environment**: dev/staging/production configurations

See **[Settings Documentation](docs/settings.md)** for complete guide and examples.

---

## 📝 Centralized Logging (New!)

Simple, unified logging system for all your applications with multiple handler support:

```python
from core_lib.tracing.logger import setup_logging, get_module_logger

# Setup at application startup
setup_logging(app_name="my-app", level="INFO")

# Use in any module
logger = get_module_logger()
logger.info("Application started")
logger.debug("Debug information")
```

### Available Handlers:
- **Console** - Always enabled with colored output
- **File** - Optional rotating file logging
- **OTLP** - OpenTelemetry Protocol for observability platforms
- **OVH LDP** - OVH Logs Data Platform integration

### Key Features:
- **Simple setup**: One function call at startup
- **Multiple handlers**: Console, file, OTLP, OVH LDP (all can run simultaneously)
- **Independent log levels**: DEBUG on console, INFO to OTLP (reduce costs)
- **Auto-namespacing**: Loggers automatically inherit app name
- **Environment-driven**: Full .env configuration support
- **Zero config**: Works out of the box with sensible defaults

### Quick Example with OTLP:

```python
from core_lib.config.logger_settings import LoggerSettings

settings = LoggerSettings(
    log_level="DEBUG",           # Console shows DEBUG+
    otlp_enabled=True,
    otlp_log_level="INFO",       # OTLP only gets INFO+ (save costs)
    otlp_endpoint="http://localhost:4318/v1/logs",
)

setup_logging(app_name="my-app", logger_settings=settings)
```

### Contextual Logging (Request Metadata):

Add request-specific metadata (user ID, session ID, company ID) to all logs:

```python
from core_lib.tracing import LoggingContext, FROM_FIELD_DESCRIPTION, parse_from

@app.post("/endpoint")
async def endpoint(from_: Optional[str] = Query(None, alias="from", description=FROM_FIELD_DESCRIPTION)):
    from_dict = parse_from(from_)  # Parse JSON metadata
    
    with LoggingContext(from_dict):
        logger.info("Processing request")
        # All logs include: session.id, user.id, organization.id, etc.
```

See **[Centralized Logging Guide](docs/centralized-logging.md)** for FastAPI, MCP, CLI, and web app examples.

---

## � Service Usage Tracking (New!)

Track AI service usage (LLM, embeddings, OCR) automatically with OpenTelemetry/OpenSearch - **no Langfuse span management required!**

### Key Features:
- ✅ **Automatic tracking** - No manual logging needed
- ✅ **Cost calculation** - Automatic pricing for OpenAI, Gemini, etc.
- ✅ **Token metrics** - Input/output tokens, latency, throughput
- ✅ **User context** - Automatically includes user_id, session_id, company_id
- ✅ **No span errors** - Uses standard logging, not Langfuse contexts
- ✅ **OpenSearch ready** - Query and visualize in dashboards

### Quick Start:

```python
from core_lib.config.logger_settings import LoggerSettings
from core_lib.tracing import setup_logging, LoggingContext
from core_lib.llm import create_openai_client

# 1. Enable OTLP logging
settings = LoggerSettings(
    otlp_enabled=True,
    otlp_endpoint="http://localhost:4318/v1/logs",
)
setup_logging(logger_settings=settings)

# 2. Use LLM client (tracking is automatic!)
client = create_openai_client(model="gpt-4o-mini")

# 3. Optional: Add user context
with LoggingContext({"user_id": "user-123", "session_id": "sess-456"}):
    response = client.chat(messages=[{"role": "user", "content": "Hello"}])
    # Automatically logs: tokens, cost, latency, user context!
```

### What Gets Tracked:

Every LLM/embedding request automatically logs:
- Service type, provider, model
- Token usage (input, output, total)
- **Automatic cost calculation** (OpenAI, Gemini, etc.)
- Performance metrics (latency, tokens/second)
- Request context (user_id, session_id, company_id)
- Feature flags (structured output, tools, search grounding)

### Example OpenSearch Query:

```json
GET /logs-*/_search
{
  "size": 0,
  "query": {"range": {"@timestamp": {"gte": "now-24h"}}},
  "aggs": {
    "total_cost": {"sum": {"field": "attributes.cost_usd"}},
    "by_service": {
      "terms": {"field": "attributes.service.type"},
      "aggs": {"cost": {"sum": {"field": "attributes.cost_usd"}}}
    }
  }
}
```

See **[Service Usage Tracking Guide](docs/SERVICE_USAGE_TRACKING.md)** for complete documentation, OpenSearch queries, and dashboard examples.

---

## �🔧 Installation

### From GitHub (recommended for external tools)

```bash
pip install git+https://github.com/Aiuj/core-lib.git@v0.2.3
```

### Using uv

```bash
uv add git+https://github.com/Aiuj/core-lib.git@v0.2.3
```

### For local development

```bash
# Clone the repository
git clone https://github.com/Aiuj/core-lib.git
cd core-lib

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
        "../core-lib"
    ]
}
```

VS Code setup for the best dev experience

- Open both repos in one VS Code workspace (so Copilot and Pylance “see” both):
  - File → Add Folder to Workspace… (add your main application AND ../core-lib)
  - Save as a .code-workspace file.

### In pyproject.toml

Add the library and a local override source in pyproject.toml

```toml
[project]
dependencies = [
  "core-lib @ git+https://github.com/Aiuj/core-lib.git"
]

[tool.uv.sources]
core-lib = { path = "../core-lib", editable = true }
```


### In requirements.txt

```txt
git+https://github.com/Aiuj/core-lib.git@v0.2.3#egg=core-lib
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

### Settings Management

Unified configuration for all services:

```python
from core_lib.config import StandardSettings

# Load all settings from environment
settings = StandardSettings.from_env()

# Use with existing clients - backward compatible
if settings.llm:
    llm_config = settings.get_llm_config()  # Returns OpenAIConfig/GeminiConfig/etc.
if settings.cache:
    redis_config = settings.get_redis_config()  # Returns RedisConfig

# Or access settings directly
print(f"App: {settings.app_name} v{settings.version}")
print(f"LLM Model: {settings.llm.model if settings.llm else 'Not configured'}")
```

### Settings Singleton Manager

Manage a single global Settings instance throughout your application:

```python
from core_lib.config import initialize_settings, get_settings
from dataclasses import dataclass

# Initialize once at application startup
settings = initialize_settings(
    app_name="my-app",
    log_level="INFO",
    enable_cache=True
)

# Access anywhere in your application
def some_function():
    config = get_settings()
    print(config.app_name)

# With custom settings class
@dataclass(frozen=True)
class MySettings(StandardSettings):
    api_key: str = ""
    max_retries: int = 3

settings = initialize_settings(
    settings_class=MySettings,
    api_key="secret"
)
```

**Key features:**
- Thread-safe singleton pattern
- Easy initialization and global access
- Support for custom settings classes
- Reset/reconfigure capabilities for testing

See **[Settings Singleton Documentation](docs/settings_singleton.md)** for complete guide.

### Cache Manager

```python
from core_lib import RedisCache, set_cache, cache_get, cache_set

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

### Job Queue System (New!)

Async job processing with Redis-based queue:

```python
from core_lib.jobs import submit_job, get_job_status, JobWorker, JobHandler

# Submit a job
job_id = submit_job(
    job_type="process_data",
    input_data={"param": "value"},
    company_id="company1"
)

# Check status
job = get_job_status(job_id)
print(f"Status: {job.status.value}, Progress: {job.progress}%")

# Create a worker
class DataProcessorHandler(JobHandler):
    def get_job_type(self):
        return "process_data"
    
    def handle(self, job):
        # Process job
        return {"result": "success"}

worker = JobWorker()
worker.register_handler(DataProcessorHandler())
worker.start()  # Blocks and processes jobs
```

See **[Job Queue Documentation](docs/JOB_QUEUE_QUICK_REFERENCE.md)** for complete guide.

### Time-based Authentication (New!)

Secure HMAC-based authentication for FastAPI and MCP servers without centralized key management:

```python
# Server setup (FastAPI)
from fastapi import FastAPI
from core_lib.api_utils.fastapi_auth import TimeBasedAuthMiddleware
from core_lib.config import AuthSettings

app = FastAPI()
settings = AuthSettings.from_env()  # AUTH_ENABLED=true, AUTH_PRIVATE_KEY=...

app.add_middleware(TimeBasedAuthMiddleware, settings=settings)

# Client setup
from core_lib.api_utils import generate_time_key

auth_key = generate_time_key(settings.auth_private_key)
headers = {settings.auth_key_header_name: auth_key}
```

**Key Features:**
- **3-hour validity window** - Keys valid for previous, current, and next hour
- **No disruptions** - Smooth transitions at hour boundaries
- **HMAC-SHA256** - Cryptographically secure with constant-time comparison
- **Simple config** - Just set `AUTH_PRIVATE_KEY` environment variable
- **FastAPI & MCP support** - Ready-to-use middleware and helpers

See **[API Authentication Documentation](docs/API_AUTH_QUICK_REFERENCE.md)** for complete guide.

### FastAPI OpenAPI Utilities (New!)

Add API key authentication to Swagger UI with a single function call:

```python
from fastapi import FastAPI
from core_lib.api_utils.fastapi_openapi import configure_api_key_auth
from core_lib.api_utils.fastapi_auth import TimeBasedAuthMiddleware
from core_lib.config import AuthSettings

app = FastAPI(title="My API", version="1.0.0")
settings = AuthSettings.from_env()

# Add "Authorize" button to Swagger UI
configure_api_key_auth(
    app,
    header_name=settings.auth_key_header_name,
    description="Time-based HMAC authentication key"
)

# Add authentication middleware
app.add_middleware(TimeBasedAuthMiddleware, settings=settings)
```

**Features:**
- **One function call** - No manual OpenAPI schema manipulation
- **Swagger UI integration** - "Authorize" button appears automatically
- **Persistent auth** - API key saved across page refreshes
- **Flexible** - Supports API key, Bearer, OAuth2, and custom schemes
- **Customizable** - Configure excluded paths, header names, descriptions

See **[FastAPI OpenAPI Documentation](docs/FASTAPI_OPENAPI_QUICK_REFERENCE.md)** for complete guide and advanced examples.

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
from core_lib import parse_from, get_transport_from_args

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

### LLM Client

Access multiple LLM providers through a unified interface:

```python
from core_lib import create_llm_client, LLMClient

# Auto-detect from environment
client = create_llm_client()

# Or specify provider and settings
client = create_llm_client(provider="openai", model="gpt-4", temperature=0.2)

# Provider-specific creation
from core_lib import create_gemini_client, create_openai_client
gemini_client = create_gemini_client(model="gemini-pro")
openai_client = create_openai_client(model="gpt-4")

# Chat with the model
messages = [{"role": "user", "content": "Hello!"}]
response = client.chat(messages)
print(response["content"])
```

#### LLM API

- `create_llm_client(provider=None, **kwargs)`:  
  Create an LLM client. Auto-detects provider if not specified.

- `create_client_from_env()`:  
  Create client using environment variables.

- `create_openai_client(model, api_key=None, **kwargs)`:  
  Create OpenAI client.

- `create_gemini_client(model, api_key=None, **kwargs)`:  
  Create Google Gemini client.

- `create_ollama_client(model, host=None, **kwargs)`:  
  Create Ollama client for local models.

See **[LLM Documentation](docs/llm.md)** for complete guide.

### Excel Manager

Process Excel files and convert them to markdown format:

```python
from core_lib import ExcelManager

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
from core_lib.config import DOC_CATEGORIES

# Access all categories
for category in DOC_CATEGORIES:
    print(f"{category['key']}: {category['label']}")
```

#### Categories API

- `CATEGORIES_BY_KEY`: Dictionary for fast lookup by category key

### Language Utilities

```python
from core_lib import LanguageUtils

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

- **[Version Management](docs/VERSION_MANAGEMENT.md)** - 🆕 Automatic version from pyproject.toml
- **[Settings Management](docs/settings.md)** - 🆕 Unified configuration system guide
- **[Settings Singleton](docs/SETTINGS_SINGLETON_QUICK_REF.md)** - Global settings management
- **[API Authentication](docs/API_AUTH_QUICK_REFERENCE.md)** - 🆕 Time-based HMAC authentication for FastAPI/MCP
- **[Service Usage Tracking](docs/SERVICE_USAGE_TRACKING.md)** - 🆕 AI service cost and usage tracking
- **[Job Queue System](docs/JOB_QUEUE_QUICK_REFERENCE.md)** - 🆕 Async job processing with Redis
- **[Excel Manager](docs/excel_manager.md)** - Complete guide for Excel file processing
- **[Cache System](docs/cache.md)** - Redis caching configuration and usage
- **[LLM Integration](docs/llm.md)** - Multi-provider LLM client documentation
- **[Centralized Logging](docs/centralized-logging.md)** - OTLP, OVH LDP, and structured logging
- **[OTLP Quick Reference](docs/OTLP_QUICK_REFERENCE.md)** - OpenTelemetry logging setup
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
uv run pytest --cov=core_lib

# Format code
uv run black core_lib tests

# Lint code
uv run flake8 core_lib tests
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

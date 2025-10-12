# API Utils - Time-based Authentication

Secure authentication utilities for inter-application communication using time-based HMAC keys.

## Quick Start

### 1. Setup (Server & Client)

Set the same private key on both server and client:

```bash
# .env file
AUTH_ENABLED=true
AUTH_PRIVATE_KEY=your-super-secret-key-minimum-16-chars
```

### 2. Server (FastAPI)

```python
from fastapi import FastAPI
from faciliter_lib.api_utils.fastapi_auth import TimeBasedAuthMiddleware
from faciliter_lib.config import AuthSettings

app = FastAPI()
settings = AuthSettings.from_env()

app.add_middleware(TimeBasedAuthMiddleware, settings=settings)
```

### 3. Client

```python
from faciliter_lib.api_utils import generate_time_key
from faciliter_lib.config import AuthSettings

settings = AuthSettings.from_env()
auth_key = generate_time_key(settings.auth_private_key)

headers = {settings.auth_key_header_name: auth_key}
```

## Features

- ✅ **No centralized key management** - Single shared secret
- ✅ **Time-based validity** - Keys valid for 3 hours (prev, current, next)
- ✅ **Smooth transitions** - No disruptions at hour boundaries
- ✅ **Secure** - HMAC-SHA256 with constant-time comparison
- ✅ **Easy integration** - FastAPI middleware & MCP helpers
- ✅ **Simple config** - Just environment variables

## Documentation

See [docs/API_AUTH_QUICK_REFERENCE.md](../docs/API_AUTH_QUICK_REFERENCE.md) for complete documentation.

## Examples

Run the examples:
```bash
uv run python examples/example_api_auth.py
```

## Tests

```bash
uv run pytest tests/test_api_utils.py tests/test_auth_settings.py -v
```

## Modules

- `time_based_auth.py` - Core HMAC key generation and verification
- `auth_settings.py` - Configuration management
- `fastapi_auth.py` - FastAPI middleware and dependencies
- `fastmcp_auth.py` - FastMCP v2 server helpers

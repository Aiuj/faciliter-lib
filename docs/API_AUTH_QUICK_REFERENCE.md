# Time-based Authentication for API Communication

Secure authentication system for inter-application communication using time-based HMAC keys, designed for FastAPI and MCP servers.

## Overview

This authentication system provides a simple yet secure way to authenticate requests between applications without requiring a centralized API key manager. It uses HMAC-SHA256 with a shared private key to generate time-based public keys that are valid for a 3-hour window.

### Key Features

- **No centralized key management**: Share a single private key between client and server
- **Time-based validity**: Keys are valid for 3 hours (previous, current, and next hour)
- **Smooth hour transitions**: No disruptions when crossing hour boundaries
- **Security**: HMAC-SHA256 with constant-time comparison prevents timing attacks
- **Framework integration**: Ready-to-use helpers for FastAPI and MCP servers
- **Simple configuration**: Just set environment variables

## How It Works

1. **Private Key**: A secret string shared between client and server (minimum 16 characters)
2. **Time Windows**: Keys are generated based on UTC hour (e.g., "2024-01-15-14")
3. **3-Hour Validity**: Keys are accepted if valid for previous, current, or next hour
4. **HMAC Generation**: `HMAC-SHA256(private_key, time_window)` produces the public key

### Time Window Example

At 14:30 UTC on 2024-01-15:
- Keys from 13:xx are valid (previous hour)
- Keys from 14:xx are valid (current hour)
- Keys from 15:xx are valid (next hour)
- Keys from 12:xx or 16:xx are **not** valid

## Quick Start

### 1. Environment Setup

Create a `.env` file or set environment variables:

```bash
# Required
AUTH_ENABLED=true
AUTH_PRIVATE_KEY=your-super-secret-key-minimum-16-characters

# Optional
AUTH_KEY_HEADER_NAME=x-auth-key  # default
```

**Security Note**: Generate a strong random key:
```python
import secrets
private_key = secrets.token_urlsafe(32)
print(f"AUTH_PRIVATE_KEY={private_key}")
```

### 2. Server Setup (FastAPI)

#### Option A: Middleware (Protect All Routes)

```python
from fastapi import FastAPI
from faciliter_lib.api_utils.fastapi_auth import TimeBasedAuthMiddleware
from faciliter_lib.config import AuthSettings

app = FastAPI()
settings = AuthSettings.from_env()

# Add authentication middleware
app.add_middleware(
    TimeBasedAuthMiddleware,
    settings=settings,
    exclude_paths=["/health", "/docs", "/openapi.json"]
)

@app.get("/protected")
async def protected_endpoint():
    return {"message": "Authenticated!"}
```

#### Option B: Dependency (Protect Specific Routes)

```python
from fastapi import FastAPI, Depends
from faciliter_lib.api_utils.fastapi_auth import create_auth_dependency
from faciliter_lib.config import AuthSettings

app = FastAPI()
settings = AuthSettings.from_env()
verify_auth = create_auth_dependency(settings)

@app.get("/public")
async def public_endpoint():
    return {"message": "No auth required"}

@app.get("/protected", dependencies=[Depends(verify_auth)])
async def protected_endpoint():
    return {"message": "Auth required"}
```

### 3. Server Setup (FastMCP v2)

```python
from mcp import FastMCP
from faciliter_lib.api_utils.fastmcp_auth import create_auth_middleware
from faciliter_lib.config import AuthSettings

mcp = FastMCP("My Server")
settings = AuthSettings.from_env()

# Add authentication middleware
auth_middleware = create_auth_middleware(settings)
# mcp.add_middleware(auth_middleware)  # When supported by FastMCP

@mcp.tool()
def secure_tool(text: str) -> str:
    """This tool requires authentication."""
    return f"Processed: {text}"
```

### 4. Client Setup

#### HTTP Requests (FastAPI Server)

```python
import httpx
from faciliter_lib.api_utils import generate_time_key
from faciliter_lib.config import AuthSettings

settings = AuthSettings.from_env()
auth_key = generate_time_key(settings.auth_private_key)

headers = {settings.auth_key_header_name: auth_key}

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/protected",
        headers=headers
    )
```

#### MCP Client (SSE Transport)

```python
from faciliter_lib.api_utils import get_auth_headers
from faciliter_lib.config import AuthSettings

settings = AuthSettings.from_env()
headers = get_auth_headers(settings)

# Use with MCP client
# async with Client(server_url, headers=headers) as client:
#     result = await client.call_tool("my_tool")
```

#### MCP Client (stdio Transport)

```python
import subprocess
from faciliter_lib.api_utils import get_auth_env_vars
from faciliter_lib.config import AuthSettings

settings = AuthSettings.from_env()
env_vars = get_auth_env_vars(settings)

# Merge with current environment
env = {**os.environ, **env_vars}

# Start MCP server with authentication
subprocess.Popen(["mcp-server"], env=env)
```

## API Reference

### Core Functions

#### `generate_time_key(private_key, dt=None, encoding='utf-8')`

Generate a time-based authentication key.

**Parameters:**
- `private_key` (str): Secret private key (minimum 16 characters)
- `dt` (datetime, optional): Datetime to generate key for (default: current UTC time)
- `encoding` (str): String encoding (default: 'utf-8')

**Returns:** str - Hex-encoded HMAC-SHA256 key (64 characters)

**Raises:** `TimeBasedAuthError` if private key is empty

**Example:**
```python
from faciliter_lib.api_utils import generate_time_key

private_key = "my-secret-key-12345678"
auth_key = generate_time_key(private_key)
# Returns: "a1b2c3d4..." (64 hex characters)
```

#### `verify_time_key(provided_key, private_key, dt=None, encoding='utf-8')`

Verify a time-based authentication key.

**Parameters:**
- `provided_key` (str): The authentication key to verify
- `private_key` (str): Secret private key (must match generation key)
- `dt` (datetime, optional): Datetime to verify against (default: current UTC time)
- `encoding` (str): String encoding (default: 'utf-8')

**Returns:** bool - True if valid, False otherwise

**Raises:** `TimeBasedAuthError` if private key is empty

**Example:**
```python
from faciliter_lib.api_utils import verify_time_key

is_valid = verify_time_key(client_key, private_key)
if is_valid:
    print("Authentication successful")
```

### Settings

#### `AuthSettings`

Configuration class for authentication settings.

**Fields:**
- `auth_enabled` (bool): Whether authentication is enabled (default: False)
- `auth_private_key` (str, optional): The secret private key
- `auth_key_header_name` (str): HTTP header name (default: "x-auth-key")

**Methods:**
- `from_env()`: Load settings from environment variables
- `validate()`: Validate settings (raises SettingsError if invalid)
- `as_dict()`: Convert to dictionary (masks private key)

**Example:**
```python
from faciliter_lib.config import AuthSettings

# From environment
settings = AuthSettings.from_env()

# With overrides
settings = AuthSettings.from_env(
    auth_enabled=True,
    auth_private_key="my-secret-key-12345678"
)

# Direct instantiation
settings = AuthSettings(
    auth_enabled=True,
    auth_private_key="my-secret-key-12345678",
    auth_key_header_name="x-custom-auth"
)
```

### FastAPI Helpers

#### `TimeBasedAuthMiddleware`

Middleware for protecting all FastAPI routes.

**Example:**
```python
app.add_middleware(
    TimeBasedAuthMiddleware,
    settings=settings,
    exclude_paths=["/health", "/docs"]
)
```

#### `create_auth_dependency(settings)`

Create a dependency for route-level authentication.

**Example:**
```python
verify_auth = create_auth_dependency(settings)

@app.get("/protected", dependencies=[Depends(verify_auth)])
async def protected():
    ...
```

### MCP Helpers

#### `get_auth_headers(settings=None)`

Get authentication headers for HTTP/SSE requests.

**Example:**
```python
headers = get_auth_headers(settings)
# Returns: {"x-auth-key": "a1b2c3d4..."}
```

#### `get_auth_env_vars(settings=None)`

Get environment variables for stdio transport.

**Example:**
```python
env_vars = get_auth_env_vars(settings)
# Returns: {"MCP_AUTH_KEY": "a1b2c3d4..."}
```

## Security Considerations

### Best Practices

1. **Strong Private Keys**
   - Minimum 16 characters (enforced)
   - Use cryptographically random generation
   - Example: `secrets.token_urlsafe(32)`

2. **Key Storage**
   - Store in environment variables or .env files
   - **Never** commit keys to version control
   - Use different keys for different environments

3. **Key Rotation**
   - Change keys periodically
   - Update all clients and servers simultaneously
   - Consider implementing a grace period with multiple keys

4. **Network Security**
   - Use HTTPS/TLS for all network communication
   - Time-based auth protects against replay attacks within 3-hour window
   - Consider additional layers for highly sensitive operations

### Security Features

- **HMAC-SHA256**: Industry-standard cryptographic hash
- **Constant-time comparison**: Prevents timing attacks
- **Time-limited validity**: Keys expire after 3 hours
- **No key transmission**: Only HMAC output is sent over network
- **Replay protection**: Combined with HTTPS, provides strong protection

### Limitations

- **Time synchronization**: Servers and clients must have reasonably synchronized clocks (within 1-2 hours)
- **3-hour window**: Keys are valid for 3 hours (trade-off for availability)
- **Shared secret**: If private key is compromised, all authentication is compromised
- **Not suitable for**: Long-lived tokens, user authentication, public APIs

## Troubleshooting

### Authentication Fails

**Problem**: Client receives 401 Unauthorized

**Solutions:**
1. Verify private key is identical on client and server
2. Check that AUTH_ENABLED=true on server
3. Verify clock synchronization (clients and servers should be within 1 hour)
4. Check header name matches (default: x-auth-key)
5. Ensure key is at least 16 characters

### Clock Synchronization Issues

**Problem**: Valid keys are rejected

**Solution:**
```python
# Test with explicit time
from datetime import datetime, timezone
from faciliter_lib.api_utils import generate_time_key, verify_time_key

now = datetime.now(timezone.utc)
print(f"Current UTC time: {now}")

key = generate_time_key(private_key, dt=now)
is_valid = verify_time_key(key, private_key, dt=now)
print(f"Key valid: {is_valid}")
```

### Key Generation Errors

**Problem**: `TimeBasedAuthError: Private key cannot be empty`

**Solution:**
- Check AUTH_PRIVATE_KEY environment variable is set
- Ensure key has no leading/trailing whitespace
- Verify key is at least 16 characters

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTH_ENABLED` | No | `false` | Enable authentication |
| `AUTH_PRIVATE_KEY` | Yes (if enabled) | None | Secret private key (min 16 chars) |
| `AUTH_KEY_HEADER_NAME` | No | `x-auth-key` | HTTP header name for auth key |

## Testing

The library includes comprehensive tests:

```bash
# Run all authentication tests
pytest tests/test_api_utils.py tests/test_auth_settings.py -v

# Test with coverage
pytest tests/test_api_utils.py --cov=faciliter_lib.api_utils
```

## Examples

See `examples/example_api_auth.py` for complete working examples:

1. FastAPI middleware authentication
2. FastAPI dependency injection
3. FastMCP v2 server integration
4. Client authentication (HTTP and MCP)
5. Manual key verification
6. Hour transition testing
7. Production configuration guide

Run examples:
```bash
uv run python examples/example_api_auth.py
```

## Integration with Existing Code

### Adding to Existing FastAPI App

```python
# Before
app = FastAPI()

@app.get("/api/data")
async def get_data():
    return {"data": "sensitive"}

# After
from faciliter_lib.api_utils.fastapi_auth import TimeBasedAuthMiddleware
from faciliter_lib.config import AuthSettings

app = FastAPI()
settings = AuthSettings.from_env()
app.add_middleware(TimeBasedAuthMiddleware, settings=settings)

@app.get("/api/data")
async def get_data():
    return {"data": "sensitive"}  # Now protected!
```

### Adding to Existing MCP Server

```python
# Before
from mcp import FastMCP

mcp = FastMCP("My Server")

@mcp.tool()
def my_tool():
    return "result"

# After
from faciliter_lib.api_utils.fastmcp_auth import create_auth_middleware
from faciliter_lib.config import AuthSettings

mcp = FastMCP("My Server")
settings = AuthSettings.from_env()
auth_middleware = create_auth_middleware(settings)
# mcp.add_middleware(auth_middleware)

@mcp.tool()
def my_tool():
    return "result"  # Now protected!
```

## Advanced Usage

### Custom Time Windows

For testing or special use cases:

```python
from datetime import datetime, timezone
from faciliter_lib.api_utils import generate_time_key, verify_time_key

# Generate key for specific time
specific_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
key = generate_time_key(private_key, dt=specific_time)

# Verify against specific time
is_valid = verify_time_key(key, private_key, dt=specific_time)
```

### Multiple Private Keys (Key Rotation)

```python
from faciliter_lib.api_utils import verify_time_key

def verify_with_rotation(provided_key: str) -> bool:
    """Verify key against current and previous private keys."""
    keys = [
        os.getenv("AUTH_PRIVATE_KEY"),
        os.getenv("AUTH_PRIVATE_KEY_OLD"),  # Grace period
    ]
    
    for private_key in keys:
        if private_key and verify_time_key(provided_key, private_key):
            return True
    
    return False
```

### Custom Header Names

```python
# Server
settings = AuthSettings.from_env(
    auth_key_header_name="x-my-custom-auth"
)

# Client
from faciliter_lib.api_utils import generate_time_key

auth_key = generate_time_key(settings.auth_private_key)
headers = {"x-my-custom-auth": auth_key}
```

## Migration Guide

### From Static API Keys

**Before:**
```python
API_KEYS = ["key1", "key2", "key3"]

def verify_api_key(key: str) -> bool:
    return key in API_KEYS
```

**After:**
```python
from faciliter_lib.api_utils import verify_time_key
from faciliter_lib.config import AuthSettings

settings = AuthSettings.from_env()

def verify_api_key(key: str) -> bool:
    return verify_time_key(key, settings.auth_private_key)
```

**Benefits:**
- No need to manage multiple keys
- Automatic expiration
- Single shared secret
- Time-based validation

## License

Part of faciliter-lib. See main library documentation for license information.

# APIClient Base Class

## Overview

The `APIClient` base class provides a reusable foundation for building HTTP API clients with built-in authentication support. It's designed to be inherited by custom API client classes and handles all authentication logic automatically.

## Features

- **Time-based HMAC authentication** (recommended) - Secure, time-limited auth
- **Legacy API key authentication** - Backward compatibility
- **No authentication** - For public APIs
- **Automatic header generation** - Auth headers added automatically
- **Standardized error handling** - Consistent error responses
- **SSL verification control** - Disable for self-signed certificates
- **Configurable timeouts** - Per-client or per-request

## Quick Start

### Basic Usage

```python
from faciliter_lib.api_utils import APIClient

# Create a simple client with time-based auth
client = APIClient(
    base_url="https://api.example.com",
    auth_enabled=True,
    auth_private_key="your-secret-key-minimum-16-chars"
)

# Prepare headers for requests
headers = client._prepare_headers()

# Use with httpx
import httpx
response = httpx.get(
    f"{client.base_url}/endpoint",
    headers=headers
)
```

### Creating a Custom API Client

```python
from faciliter_lib.api_utils import APIClient
from typing import Dict, Any

class MyAPIClient(APIClient):
    """Custom API client inheriting from APIClient."""
    
    def get_data(self, item_id: str) -> Dict[str, Any]:
        """Get data by ID."""
        try:
            headers = self._prepare_headers()
            
            with self._create_client() as client:
                response = client.get(
                    f"{self.base_url}/items/{item_id}",
                    headers=headers
                )
                response.raise_for_status()
                
                return {
                    "success": True,
                    "data": response.json()
                }
        except Exception as e:
            return self._handle_response_error(e, operation=f"getting item {item_id}")
```

## Constructor Parameters

```python
APIClient(
    base_url: str,
    api_key: Optional[str] = None,
    auth_enabled: bool = False,
    auth_private_key: Optional[str] = None,
    auth_header_name: str = "x-auth-key",
    api_key_header_name: str = "x-api-key",
    timeout: float = 30.0,
    verify_ssl: bool = True,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | *required* | Base URL of the API (e.g., `http://localhost:9095`) |
| `api_key` | Optional[str] | None | Static API key for legacy authentication |
| `auth_enabled` | bool | False | Enable time-based HMAC authentication |
| `auth_private_key` | Optional[str] | None | Private key for time-based auth (required if `auth_enabled=True`) |
| `auth_header_name` | str | `"x-auth-key"` | HTTP header name for time-based auth |
| `api_key_header_name` | str | `"x-api-key"` | HTTP header name for legacy API key |
| `timeout` | float | 30.0 | Default request timeout in seconds |
| `verify_ssl` | bool | True | Whether to verify SSL certificates |

## Protected Methods

### `_prepare_headers(additional_headers=None, skip_auth=False)`

Prepare HTTP headers with authentication.

```python
# Basic usage
headers = client._prepare_headers()

# With additional custom headers
headers = client._prepare_headers(
    additional_headers={"X-Request-ID": "12345"}
)

# Skip authentication for public endpoints
headers = client._prepare_headers(skip_auth=True)
```

**Returns:** `Dict[str, str]` - Dictionary of HTTP headers

**Raises:** `Exception` if time-based auth key generation fails

### `_handle_response_error(error, operation="")`

Handle HTTP errors and convert to standardized response.

```python
try:
    response = client.get(url)
    response.raise_for_status()
except Exception as e:
    return client._handle_response_error(e, operation="getting data")
```

**Returns:** `Dict[str, Any]` with structure:
```python
{
    "success": False,
    "error_code": str,  # HTTP_404, TIMEOUT_ERROR, REQUEST_ERROR, etc.
    "error_description": str,
    "status_code": int  # Only for HTTP errors
}
```

### `_create_client(timeout=None)`

Create an httpx.Client with default settings.

```python
with client._create_client() as http_client:
    response = http_client.get(url)
```

**Parameters:**
- `timeout` (Optional[float]): Override default timeout

**Returns:** `httpx.Client` instance

### `_get_auth_method()`

Get the current authentication method as a string.

```python
auth_method = client._get_auth_method()
# Returns: "time-based HMAC", "static API key", or "none"
```

## Authentication Priority

The client uses authentication in this priority order:

1. **Time-based HMAC** (if `auth_enabled=True` and `auth_private_key` is set)
2. **Legacy API key** (if `api_key` is set)
3. **No authentication**

## Environment-Based Configuration

Use a custom prefix for environment variables:

```python
import os
from faciliter_lib.api_utils import APIClient

def create_api_client_from_env(prefix: str) -> APIClient:
    """Create API client from environment variables."""
    return APIClient(
        base_url=os.getenv(f"{prefix}_URL"),
        api_key=os.getenv(f"{prefix}_KEY"),
        auth_enabled=os.getenv(f"{prefix}_AUTH_ENABLED", "false").lower() == "true",
        auth_private_key=os.getenv(f"{prefix}_AUTH_PRIVATE_KEY"),
        auth_header_name=os.getenv(f"{prefix}_AUTH_HEADER_NAME", "x-auth-key")
    )

# Usage with KB_API_ prefix
client = create_api_client_from_env("KB_API")
```

**Environment variables:**
```bash
KB_API_URL=http://localhost:9095
KB_API_AUTH_ENABLED=true
KB_API_AUTH_PRIVATE_KEY=your-secret-key
KB_API_AUTH_HEADER_NAME=x-auth-key  # Optional
```

## Complete Example

```python
from faciliter_lib.api_utils import APIClient
from typing import Dict, Any, List

class UserAPIClient(APIClient):
    """User management API client."""
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        try:
            headers = self._prepare_headers()
            
            with self._create_client() as client:
                response = client.post(
                    f"{self.base_url}/users",
                    json=user_data,
                    headers=headers
                )
                response.raise_for_status()
                
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code
                }
        except Exception as e:
            return self._handle_response_error(e, operation="creating user")
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID."""
        try:
            headers = self._prepare_headers()
            
            with self._create_client() as client:
                response = client.get(
                    f"{self.base_url}/users/{user_id}",
                    headers=headers
                )
                response.raise_for_status()
                
                return {
                    "success": True,
                    "data": response.json()
                }
        except Exception as e:
            return self._handle_response_error(e, operation=f"getting user {user_id}")

# Initialize with time-based auth
client = UserAPIClient(
    base_url="https://api.example.com",
    auth_enabled=True,
    auth_private_key="my-secret-key-minimum-16-chars"
)

# Use the client
result = client.create_user({
    "name": "John Doe",
    "email": "john@example.com"
})

if result["success"]:
    print(f"User created: {result['data']}")
else:
    print(f"Error: {result['error_description']}")
```

## Best Practices

### 1. Always Use Try-Except

```python
def my_api_method(self):
    try:
        headers = self._prepare_headers()
        # ... make request
        return {"success": True, "data": data}
    except Exception as e:
        return self._handle_response_error(e, operation="operation description")
```

### 2. Provide Descriptive Operation Names

```python
# Good
self._handle_response_error(e, operation="getting user profile")

# Bad
self._handle_response_error(e, operation="get")
```

### 3. Use Context Manager for HTTP Client

```python
# Good
with self._create_client() as client:
    response = client.get(url)

# Avoid
client = self._create_client()
response = client.get(url)
client.close()  # May not be called if exception occurs
```

### 4. Skip Auth for Public Endpoints

```python
def get_public_status(self):
    headers = self._prepare_headers(skip_auth=True)
    # ... make request to public endpoint
```

### 5. Add Custom Headers When Needed

```python
def request_with_correlation_id(self, correlation_id: str):
    headers = self._prepare_headers(
        additional_headers={"X-Correlation-ID": correlation_id}
    )
    # ... make request
```

## Error Handling

The `_handle_response_error` method returns standardized error responses:

### HTTP Errors
```python
{
    "success": False,
    "error_code": "HTTP_404",
    "error_description": "HTTP 404: Not Found",
    "status_code": 404
}
```

### Timeout Errors
```python
{
    "success": False,
    "error_code": "TIMEOUT_ERROR",
    "error_description": "Request timeout after 30.0s: ..."
}
```

### Network Errors
```python
{
    "success": False,
    "error_code": "REQUEST_ERROR",
    "error_description": "Network/connection error: ..."
}
```

### Unexpected Errors
```python
{
    "success": False,
    "error_code": "UNEXPECTED_ERROR",
    "error_description": "Unexpected error: ValueError - ..."
}
```

## Testing

```python
import pytest
from my_module import MyAPIClient

def test_client_initialization():
    client = MyAPIClient(
        base_url="https://api.test.com",
        auth_enabled=True,
        auth_private_key="test-key-16-chars"
    )
    
    assert client.base_url == "https://api.test.com"
    assert client.auth_enabled is True
    assert client._get_auth_method() == "time-based HMAC"

def test_header_generation():
    client = MyAPIClient(
        base_url="https://api.test.com",
        auth_enabled=True,
        auth_private_key="test-key-16-chars"
    )
    
    headers = client._prepare_headers()
    assert "x-auth-key" in headers
    assert "Content-Type" in headers
    assert len(headers["x-auth-key"]) == 64  # HMAC-SHA256 hex
```

## Examples

See `examples/example_api_client_usage.py` for comprehensive examples including:
- Simple API client with time-based auth
- API client with multiple endpoints
- Environment-based configuration
- Custom headers and conditional auth
- Public and private endpoints

## Related Documentation

- [Time-Based Authentication](API_AUTH_QUICK_REFERENCE.md) - HMAC auth system details
- [KB API Authentication](../../agent-rfx/docs/KB_API_AUTHENTICATION.md) - Real-world usage example

## License

Part of faciliter-lib. See main library documentation for license information.

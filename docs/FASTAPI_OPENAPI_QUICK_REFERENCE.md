# FastAPI OpenAPI Customization Quick Reference

Utilities for customizing FastAPI's OpenAPI schema, particularly for adding security schemes to Swagger UI.

## Installation

These utilities are part of `faciliter_lib.api_utils` and require FastAPI to be installed:

```bash
pip install fastapi
```

## Quick Start

### Basic API Key Authentication

```python
from fastapi import FastAPI
from faciliter_lib.api_utils.fastapi_openapi import configure_api_key_auth
from faciliter_lib.api_utils.fastapi_auth import TimeBasedAuthMiddleware
from faciliter_lib.config import AuthSettings

app = FastAPI(title="My API", version="1.0.0")

# Configure API key authentication in Swagger UI
configure_api_key_auth(app)

# Add authentication middleware
settings = AuthSettings.from_env()
app.add_middleware(
    TimeBasedAuthMiddleware,
    settings=settings,
    exclude_paths=["/health", "/docs", "/openapi.json"]
)
```

Now when you open `/docs`, you'll see an "Authorize" button where you can enter your API key.

## API Reference

### `configure_api_key_auth()`

Configures API key authentication for Swagger UI with sensible defaults.

**Parameters:**
- `app` (FastAPI): FastAPI application instance
- `header_name` (str): Name of the header for the API key (default: `"x-api-key"`)
- `security_scheme_name` (str): Name in OpenAPI schema (default: `"ApiKeyAuth"`)
- `description` (str): Description shown in Swagger UI (default: `"API Key authentication"`)
- `exclude_paths` (List[str]): Paths to exclude from auth (default: `["/health", "/docs", "/openapi.json", "/redoc"]`)
- `persist_authorization` (bool): Keep auth across page refreshes (default: `True`)

**Example:**
```python
configure_api_key_auth(
    app,
    header_name="x-custom-api-key",
    description="Time-based HMAC authentication key",
    exclude_paths=["/health", "/metrics"]
)
```

### `add_custom_security_scheme()`

Adds any type of security scheme (API key, OAuth2, HTTP Bearer, etc.) to the OpenAPI schema.

**Parameters:**
- `app` (FastAPI): FastAPI application instance
- `scheme_name` (str): Name of the security scheme in OpenAPI
- `scheme_definition` (Dict[str, Any]): OpenAPI security scheme definition
- `apply_to_all` (bool): Apply to all endpoints (default: `False`)
- `exclude_paths` (List[str]): Paths to exclude when `apply_to_all=True`

**Example - Bearer Token:**
```python
from faciliter_lib.api_utils.fastapi_openapi import add_custom_security_scheme

bearer_scheme = {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT"
}

add_custom_security_scheme(
    app,
    scheme_name="BearerAuth",
    scheme_definition=bearer_scheme,
    apply_to_all=True,
    exclude_paths=["/health", "/docs", "/openapi.json"]
)
```

**Example - OAuth2:**
```python
oauth2_scheme = {
    "type": "oauth2",
    "flows": {
        "password": {
            "tokenUrl": "/token",
            "scopes": {
                "read": "Read access",
                "write": "Write access"
            }
        }
    }
}

add_custom_security_scheme(
    app,
    scheme_name="OAuth2",
    scheme_definition=oauth2_scheme,
    apply_to_all=True
)
```

## Common Use Cases

### 1. Custom Header Name

If your API uses a custom header name:

```python
from faciliter_lib.config import AuthSettings

settings = AuthSettings.from_env()
settings.auth_key_header_name = "x-custom-token"

configure_api_key_auth(
    app,
    header_name="x-custom-token",
    description="Custom authentication token"
)

app.add_middleware(
    TimeBasedAuthMiddleware,
    settings=settings,
    exclude_paths=["/health", "/docs", "/openapi.json"]
)
```

### 2. Multiple Authentication Methods

You can configure multiple authentication schemes:

```python
# API Key for service-to-service
configure_api_key_auth(
    app,
    header_name="x-api-key",
    security_scheme_name="ApiKeyAuth"
)

# Bearer token for user authentication
bearer_scheme = {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT"
}
add_custom_security_scheme(
    app,
    scheme_name="BearerAuth",
    scheme_definition=bearer_scheme
)
```

### 3. Disable Authorization Persistence

If you don't want Swagger UI to remember the API key:

```python
configure_api_key_auth(
    app,
    persist_authorization=False
)
```

### 4. Custom Excluded Paths

```python
configure_api_key_auth(
    app,
    exclude_paths=[
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/public/*"  # Exclude all public paths
    ]
)
```

## Integration with Time-Based Authentication

These utilities work seamlessly with `faciliter_lib`'s time-based authentication:

```python
from fastapi import FastAPI
from faciliter_lib.api_utils.fastapi_openapi import configure_api_key_auth
from faciliter_lib.api_utils.fastapi_auth import TimeBasedAuthMiddleware
from faciliter_lib.api_utils import generate_time_key
from faciliter_lib.config import AuthSettings

app = FastAPI()

# Configure Swagger UI
settings = AuthSettings.from_env()
configure_api_key_auth(
    app,
    header_name=settings.auth_key_header_name
)

# Add middleware
app.add_middleware(
    TimeBasedAuthMiddleware,
    settings=settings,
    exclude_paths=["/health", "/docs", "/openapi.json"]
)

# To test in Swagger UI, generate a key:
# from faciliter_lib.api_utils import generate_time_key
# key = generate_time_key("your-private-key")
# Then paste the key into the Swagger UI "Authorize" dialog
```

## Testing

To test your API with the configured authentication:

1. Start your server
2. Open `http://localhost:8000/docs` in a browser
3. Click the "Authorize" button (lock icon) at the top right
4. Enter your API key in the value field
5. Click "Authorize" and then "Close"
6. All subsequent requests will include the authentication header

## Troubleshooting

### "Authorize" button not showing
- Make sure you called `configure_api_key_auth()` before starting the server
- Check that your endpoints are not all in the `exclude_paths` list

### Authentication still required on excluded paths
- Ensure the same paths are excluded in both `configure_api_key_auth()` and the middleware
- Path matching is exact - `/health` won't match `/health/`

### API key not being sent with requests
- Check browser console for errors
- Make sure you clicked "Authorize" after entering the key
- Try disabling browser extensions that might interfere

## Examples

See `examples/example_fastapi_openapi.py` for complete working examples:
- Basic API key authentication
- Custom configuration
- Multiple authentication schemes
- OAuth2 integration

## Related

- [FastAPI Authentication Middleware](./API_AUTH_QUICK_REFERENCE.md)
- [Time-Based Authentication](./API_AUTH_QUICK_REFERENCE.md)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)

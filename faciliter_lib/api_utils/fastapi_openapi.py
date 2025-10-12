"""FastAPI OpenAPI customization utilities.

Provides utilities for customizing FastAPI's OpenAPI schema generation,
particularly for adding security schemes like API key authentication to
Swagger UI.

Example:
    ```python
    from fastapi import FastAPI
    from faciliter_lib.api_utils.fastapi_openapi import configure_api_key_auth
    from faciliter_lib.config import AuthSettings
    
    app = FastAPI()
    settings = AuthSettings.from_env()
    
    # Configure API key authentication in Swagger UI
    configure_api_key_auth(
        app,
        header_name=settings.auth_key_header_name,
        exclude_paths=["/health", "/docs", "/openapi.json"]
    )
    ```
"""

from typing import Optional, List, Dict, Any, Callable

try:
    from fastapi import FastAPI
    from fastapi.openapi.utils import get_openapi
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None  # type: ignore
    get_openapi = None  # type: ignore


def _add_security_scheme_to_openapi(
    app: "FastAPI",
    scheme_name: str,
    scheme_definition: Dict[str, Any],
    apply_to_all: bool = False,
    exclude_paths: Optional[List[str]] = None,
    preserve_existing: bool = True
) -> None:
    """Internal helper to add a security scheme to the OpenAPI schema.
    
    Args:
        app: FastAPI application instance
        scheme_name: Name of the security scheme
        scheme_definition: OpenAPI security scheme definition
        apply_to_all: Whether to apply to all endpoints
        exclude_paths: Paths to exclude from security application
        preserve_existing: Whether to preserve existing openapi function (for chaining)
    """
    if exclude_paths is None:
        exclude_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
    
    # Store the original openapi function if preserving
    original_openapi: Optional[Callable] = None
    if preserve_existing and hasattr(app, 'openapi') and callable(app.openapi):
        original_openapi = app.openapi
    
    # Reset OpenAPI schema to regenerate
    app.openapi_schema = None
    
    def custom_openapi() -> Dict[str, Any]:
        """Generate customized OpenAPI schema with security scheme."""
        if app.openapi_schema:
            return app.openapi_schema
        
        # Call original openapi function if it exists, otherwise generate base schema
        if original_openapi and callable(original_openapi):
            openapi_schema = original_openapi()
        else:
            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                routes=app.routes,
            )
        
        # Ensure components and securitySchemes exist
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}
        
        # Add the security scheme
        openapi_schema["components"]["securitySchemes"][scheme_name] = scheme_definition
        
        # Apply security to endpoints if requested
        if apply_to_all:
            for path, path_item in openapi_schema.get("paths", {}).items():
                if path not in exclude_paths:
                    for method in path_item.values():
                        if isinstance(method, dict):
                            if "security" not in method:
                                method["security"] = []
                            # Add our scheme if not already present
                            security_entry = {scheme_name: []}
                            if security_entry not in method["security"]:
                                method["security"].append(security_entry)
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    # Replace the app's openapi method
    app.openapi = custom_openapi


def configure_api_key_auth(
    app: "FastAPI",
    header_name: str = "x-api-key",
    security_scheme_name: str = "ApiKeyAuth",
    description: str = "API Key authentication",
    exclude_paths: Optional[List[str]] = None,
    persist_authorization: bool = True
) -> None:
    """Configure API key authentication in FastAPI's OpenAPI schema for Swagger UI.
    
    This is a convenience function that creates an API key security scheme
    and applies it globally to all endpoints except those excluded.
    
    Args:
        app: FastAPI application instance
        header_name: Name of the header for the API key (default: "x-api-key")
        security_scheme_name: Name of the security scheme in OpenAPI (default: "ApiKeyAuth")
        description: Description shown in Swagger UI (default: "API Key authentication")
        exclude_paths: List of paths to exclude from authentication (default: ["/health", "/docs", "/openapi.json", "/redoc"])
        persist_authorization: Whether to persist authorization in Swagger UI across refreshes (default: True)
        
    Raises:
        ImportError: If FastAPI is not installed
        
    Example:
        ```python
        from fastapi import FastAPI
        from faciliter_lib.api_utils.fastapi_openapi import configure_api_key_auth
        
        app = FastAPI()
        
        # Basic configuration with defaults
        configure_api_key_auth(app)
        
        # Custom configuration
        configure_api_key_auth(
            app,
            header_name="x-custom-api-key",
            description="Custom authentication token",
            exclude_paths=["/health", "/metrics"]
        )
        ```
    """
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI is required for configure_api_key_auth. "
            "Install it with: pip install fastapi"
        )
    
    # Configure Swagger UI to persist authorization
    if persist_authorization:
        if not hasattr(app, 'swagger_ui_parameters') or app.swagger_ui_parameters is None:
            app.swagger_ui_parameters = {}
        app.swagger_ui_parameters["persistAuthorization"] = True
    
    # Create API key security scheme definition
    api_key_scheme = {
        "type": "apiKey",
        "in": "header",
        "name": header_name,
        "description": description
    }
    
    # Use the internal helper to add the scheme
    _add_security_scheme_to_openapi(
        app=app,
        scheme_name=security_scheme_name,
        scheme_definition=api_key_scheme,
        apply_to_all=True,
        exclude_paths=exclude_paths,
        preserve_existing=False
    )


def add_custom_security_scheme(
    app: "FastAPI",
    scheme_name: str,
    scheme_definition: Dict[str, Any],
    apply_to_all: bool = False,
    exclude_paths: Optional[List[str]] = None
) -> None:
    """Add a custom security scheme to FastAPI's OpenAPI schema.
    
    This is a flexible function that allows adding any type of security
    scheme (API key, OAuth2, HTTP Bearer, etc.) to the OpenAPI schema.
    Can be called multiple times to add different schemes.
    
    Args:
        app: FastAPI application instance
        scheme_name: Name of the security scheme in OpenAPI
        scheme_definition: OpenAPI security scheme definition dict
        apply_to_all: Whether to apply the security scheme to all endpoints (default: False)
        exclude_paths: List of paths to exclude when apply_to_all is True
        
    Raises:
        ImportError: If FastAPI is not installed
        
    Example:
        ```python
        from fastapi import FastAPI
        from faciliter_lib.api_utils.fastapi_openapi import add_custom_security_scheme
        
        app = FastAPI()
        
        # Add OAuth2 scheme
        oauth2_scheme = {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/token",
                    "scopes": {"read": "Read access", "write": "Write access"}
                }
            }
        }
        add_custom_security_scheme(app, "OAuth2", oauth2_scheme, apply_to_all=True)
        
        # Add Bearer token scheme (can chain multiple schemes)
        bearer_scheme = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
        add_custom_security_scheme(app, "BearerAuth", bearer_scheme)
        ```
    """
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI is required for add_custom_security_scheme. "
            "Install it with: pip install fastapi"
        )
    
    # Use the internal helper, preserving any existing openapi function
    _add_security_scheme_to_openapi(
        app=app,
        scheme_name=scheme_name,
        scheme_definition=scheme_definition,
        apply_to_all=apply_to_all,
        exclude_paths=exclude_paths,
        preserve_existing=True
    )

"""Example demonstrating FastAPI OpenAPI customization utilities.

This example shows how to use configure_api_key_auth and add_custom_security_scheme
to add authentication to Swagger UI in FastAPI applications.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from core_lib.api_utils.fastapi_auth import TimeBasedAuthMiddleware
from core_lib.api_utils.fastapi_openapi import configure_api_key_auth, add_custom_security_scheme
from core_lib.config import AuthSettings


# Example 1: Basic API key authentication with Swagger UI
def example_basic_api_key_auth():
    """Simple example with default settings."""
    app = FastAPI(title="Basic API Key Example", version="1.0.0")
    
    # Configure API key authentication for Swagger UI
    configure_api_key_auth(app)
    
    # Add the middleware
    settings = AuthSettings.from_env()
    app.add_middleware(
        TimeBasedAuthMiddleware,
        settings=settings,
        exclude_paths=["/health", "/docs", "/openapi.json", "/redoc"]
    )
    
    @app.get("/protected")
    async def protected_endpoint():
        return {"message": "This endpoint requires authentication"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app


# Example 2: Custom API key configuration
def example_custom_api_key_auth():
    """Example with custom header name and description."""
    app = FastAPI(title="Custom API Key Example", version="1.0.0")
    
    # Custom configuration
    configure_api_key_auth(
        app,
        header_name="x-custom-token",
        description="Custom time-based authentication token",
        exclude_paths=["/health", "/metrics"],
        persist_authorization=True
    )
    
    # Add middleware with custom settings
    settings = AuthSettings.from_env()
    settings.auth_key_header_name = "x-custom-token"  # Match the header name
    
    app.add_middleware(
        TimeBasedAuthMiddleware,
        settings=settings,
        exclude_paths=["/health", "/metrics"]
    )
    
    @app.get("/protected")
    async def protected_endpoint():
        return {"message": "Protected with custom header"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app


# Example 3: Multiple authentication schemes
def example_multiple_auth_schemes():
    """Example showing how to add multiple authentication schemes."""
    app = FastAPI(title="Multiple Auth Schemes Example", version="1.0.0")
    
    # First, configure API key auth
    configure_api_key_auth(
        app,
        header_name="x-api-key",
        security_scheme_name="ApiKeyAuth",
        description="API Key for service-to-service communication"
    )
    
    # Then add Bearer token auth
    bearer_scheme = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token for user authentication"
    }
    add_custom_security_scheme(
        app,
        scheme_name="BearerAuth",
        scheme_definition=bearer_scheme,
        apply_to_all=False  # Don't apply globally, we'll use dependencies
    )
    
    # You can now use either authentication method in your endpoints
    # via dependencies or manually in Swagger UI
    
    @app.get("/api-key-protected")
    async def api_key_protected():
        """Protected by API key."""
        return {"message": "Protected by API key"}
    
    @app.get("/bearer-protected")
    async def bearer_protected():
        """Protected by Bearer token."""
        return {"message": "Protected by Bearer token"}
    
    return app


# Example 4: OAuth2 authentication
def example_oauth2_auth():
    """Example with OAuth2 authentication scheme."""
    app = FastAPI(title="OAuth2 Example", version="1.0.0")
    
    # Define OAuth2 scheme
    oauth2_scheme = {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "/token",
                "scopes": {
                    "read": "Read access to resources",
                    "write": "Write access to resources",
                    "admin": "Administrative access"
                }
            }
        }
    }
    
    add_custom_security_scheme(
        app,
        scheme_name="OAuth2PasswordBearer",
        scheme_definition=oauth2_scheme,
        apply_to_all=True,
        exclude_paths=["/health", "/docs", "/openapi.json", "/token"]
    )
    
    @app.post("/token")
    async def login(username: str, password: str):
        """Token endpoint (not actually implemented)."""
        return {"access_token": "fake_token", "token_type": "bearer"}
    
    @app.get("/protected")
    async def protected_endpoint():
        return {"message": "OAuth2 protected endpoint"}
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Run one of the examples (change this to test different examples)
    app = example_basic_api_key_auth()
    
    print("Starting FastAPI server with API key authentication...")
    print("Open http://localhost:8000/docs to see Swagger UI")
    print("Click the 'Authorize' button to enter your API key")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

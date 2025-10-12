"""FastMCP v2 utilities for time-based authentication.

Provides utilities for securing FastMCP v2 servers with time-based
HMAC authentication, compatible with both SSE and stdio transports.

Example:
    Server side (FastMCP v2):
        ```python
        from mcp import FastMCP
        from faciliter_lib.api_utils.fastmcp_auth import create_auth_middleware
        from faciliter_lib.config import AuthSettings
        
        mcp = FastMCP("My MCP Server")
        settings = AuthSettings.from_env()
        
        # Add authentication middleware
        auth_middleware = create_auth_middleware(settings)
        mcp.add_middleware(auth_middleware)
        
        @mcp.tool()
        def my_tool():
            return "Authenticated access"
        ```
    
    Client side:
        ```python
        from faciliter_lib.api_utils import generate_time_key
        from faciliter_lib.config import AuthSettings
        
        settings = AuthSettings.from_env()
        auth_key = generate_time_key(settings.auth_private_key)
        
        # For SSE transport
        headers = {settings.auth_key_header_name: auth_key}
        
        # For stdio, pass as environment variable
        env = {"MCP_AUTH_KEY": auth_key}
        ```
"""

from typing import Optional, Dict, Any, Callable
import os

from .time_based_auth import verify_time_key, TimeBasedAuthError
from .auth_settings import AuthSettings


class MCPAuthError(Exception):
    """Raised when MCP authentication fails."""
    pass


def create_auth_middleware(settings: AuthSettings):
    """Create authentication middleware for FastMCP v2 servers.
    
    This middleware validates time-based auth keys for incoming requests.
    Works with both SSE (HTTP headers) and stdio (environment variables).
    
    Args:
        settings: AuthSettings instance with private key
        
    Returns:
        Middleware function compatible with FastMCP v2
        
    Example:
        ```python
        from mcp import FastMCP
        
        mcp = FastMCP("server")
        settings = AuthSettings.from_env()
        
        auth_middleware = create_auth_middleware(settings)
        # Note: Actual middleware integration depends on FastMCP v2 API
        ```
    """
    async def auth_middleware(context: Dict[str, Any], next_handler: Callable):
        """Validate authentication before processing request."""
        # Skip if authentication is disabled
        if not settings.auth_enabled:
            return await next_handler(context)
        
        # Try to get auth key from different sources
        auth_key = None
        
        # 1. Check HTTP headers (for SSE transport)
        if "headers" in context:
            headers = context.get("headers", {})
            auth_key = headers.get(settings.auth_key_header_name)
        
        # 2. Check environment variable (for stdio transport)
        if not auth_key:
            auth_key = os.environ.get("MCP_AUTH_KEY")
        
        # 3. Check context metadata
        if not auth_key and "metadata" in context:
            metadata = context.get("metadata", {})
            auth_key = metadata.get("auth_key")
        
        if not auth_key:
            raise MCPAuthError(
                f"Missing authentication. Provide {settings.auth_key_header_name} "
                f"header or MCP_AUTH_KEY environment variable."
            )
        
        # Verify the time-based key
        try:
            if not verify_time_key(auth_key, settings.auth_private_key):
                raise MCPAuthError("Invalid or expired authentication key")
        except TimeBasedAuthError as e:
            raise MCPAuthError(f"Authentication error: {e}")
        
        # Authentication successful, proceed with request
        return await next_handler(context)
    
    return auth_middleware


def verify_mcp_auth(
    auth_key: Optional[str],
    settings: Optional[AuthSettings] = None,
    private_key: Optional[str] = None
) -> bool:
    """Verify MCP authentication key.
    
    Convenience function for manual authentication validation in MCP tools.
    
    Args:
        auth_key: The authentication key to verify
        settings: AuthSettings instance (if not provided, uses private_key)
        private_key: Private key for verification (if settings not provided)
        
    Returns:
        True if authentication is valid or disabled, False otherwise
        
    Raises:
        ValueError: If neither settings nor private_key is provided
        
    Example:
        ```python
        @mcp.tool()
        def sensitive_operation(auth_key: str = None):
            settings = AuthSettings.from_env()
            if not verify_mcp_auth(auth_key, settings=settings):
                raise ValueError("Authentication failed")
            
            return perform_operation()
        ```
    """
    # Load settings if not provided
    if settings is None and private_key is None:
        settings = AuthSettings.from_env()
    
    # Use settings if provided
    if settings is not None:
        if not settings.auth_enabled:
            return True
        private_key = settings.auth_private_key
    
    if not private_key:
        raise ValueError("Either settings or private_key must be provided")
    
    if not auth_key:
        return False
    
    try:
        return verify_time_key(auth_key, private_key)
    except TimeBasedAuthError:
        return False


def get_auth_headers(settings: Optional[AuthSettings] = None) -> Dict[str, str]:
    """Generate authentication headers for MCP client requests.
    
    Creates a dictionary with the authentication header that can be
    added to HTTP requests or MCP client configuration.
    
    Args:
        settings: AuthSettings instance (if None, loads from environment)
        
    Returns:
        Dictionary with authentication header
        
    Example:
        ```python
        from mcp import Client
        
        settings = AuthSettings.from_env()
        headers = get_auth_headers(settings)
        
        # Use with HTTP client
        async with Client(server_url, headers=headers) as client:
            result = await client.call_tool("my_tool")
        ```
    """
    if settings is None:
        settings = AuthSettings.from_env()
    
    if not settings.auth_enabled or not settings.auth_private_key:
        return {}
    
    from .time_based_auth import generate_time_key
    
    auth_key = generate_time_key(settings.auth_private_key)
    return {settings.auth_key_header_name: auth_key}


def get_auth_env_vars(settings: Optional[AuthSettings] = None) -> Dict[str, str]:
    """Generate authentication environment variables for MCP stdio transport.
    
    Creates environment variables that can be passed to MCP server processes
    using stdio transport.
    
    Args:
        settings: AuthSettings instance (if None, loads from environment)
        
    Returns:
        Dictionary with MCP_AUTH_KEY environment variable
        
    Example:
        ```python
        import subprocess
        
        settings = AuthSettings.from_env()
        env_vars = get_auth_env_vars(settings)
        
        # Merge with current environment
        env = {**os.environ, **env_vars}
        
        # Start MCP server with authentication
        subprocess.Popen(["mcp-server"], env=env)
        ```
    """
    if settings is None:
        settings = AuthSettings.from_env()
    
    if not settings.auth_enabled or not settings.auth_private_key:
        return {}
    
    from .time_based_auth import generate_time_key
    
    auth_key = generate_time_key(settings.auth_private_key)
    return {"MCP_AUTH_KEY": auth_key}

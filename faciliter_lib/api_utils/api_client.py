"""
Base API Client with Time-Based Authentication

Provides a reusable base class for HTTP API clients with built-in support
for time-based HMAC authentication, legacy API key authentication, and no auth.
"""

import httpx
from typing import Optional, Dict, Any
from .time_based_auth import generate_time_key

try:
    from faciliter_lib import get_module_logger
    logger = get_module_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class APIClient:
    """Base API client with time-based authentication support.
    
    This class provides a foundation for building HTTP API clients with
    built-in authentication handling. It supports:
    - Time-based HMAC authentication (recommended)
    - Legacy static API key authentication
    - No authentication
    
    Authentication priority:
    1. Time-based auth (if auth_enabled=True and auth_private_key is set)
    2. Legacy API key (if api_key is set)
    3. No authentication
    
    Example:
        class MyAPIClient(APIClient):
            def get_data(self, item_id: str):
                headers = self._prepare_headers()
                response = httpx.get(
                    f"{self.base_url}/items/{item_id}",
                    headers=headers
                )
                return response.json()
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        auth_enabled: bool = False,
        auth_private_key: Optional[str] = None,
        auth_header_name: str = "x-auth-key",
        api_key_header_name: str = "x-api-key",
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API (e.g., http://localhost:9095)
            api_key: Optional static API key for legacy authentication
            auth_enabled: Enable time-based HMAC authentication
            auth_private_key: Private key for time-based auth (required if auth_enabled=True)
            auth_header_name: HTTP header name for time-based auth (default: x-auth-key)
            api_key_header_name: HTTP header name for legacy API key (default: x-api-key)
            timeout: Default request timeout in seconds
            verify_ssl: Whether to verify SSL certificates (set False for self-signed certs)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.auth_enabled = auth_enabled
        self.auth_private_key = auth_private_key
        self.auth_header_name = auth_header_name
        self.api_key_header_name = api_key_header_name
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Determine authentication method for logging
        auth_method = self._get_auth_method()
        logger.info(f"Initialized API client for {base_url} with auth: {auth_method}")
    
    def _get_auth_method(self) -> str:
        """Get the current authentication method as a string."""
        if self.auth_enabled and self.auth_private_key:
            return "time-based HMAC"
        elif self.api_key:
            return "static API key"
        else:
            return "none"
    
    def _prepare_headers(
        self,
        additional_headers: Optional[Dict[str, str]] = None,
        skip_auth: bool = False
    ) -> Dict[str, str]:
        """
        Prepare HTTP headers with authentication.
        
        Args:
            additional_headers: Optional additional headers to include
            skip_auth: If True, skip adding authentication headers
            
        Returns:
            Dictionary of HTTP headers ready for use
            
        Raises:
            Exception: If time-based auth key generation fails
        """
        headers = {"Content-Type": "application/json"}
        
        # Add additional headers if provided
        if additional_headers:
            headers.update(additional_headers)
        
        # Skip authentication if requested
        if skip_auth:
            return headers
        
        # Add authentication header based on configuration
        if self.auth_enabled and self.auth_private_key:
            # Use time-based HMAC authentication
            try:
                auth_key = generate_time_key(self.auth_private_key)
                headers[self.auth_header_name] = auth_key
                logger.debug(f"Generated time-based auth key for API request")
            except Exception as e:
                logger.error(f"Failed to generate time-based auth key: {e}")
                raise
        elif self.api_key:
            # Fall back to legacy API key authentication
            headers[self.api_key_header_name] = self.api_key
            logger.debug(f"Using legacy API key authentication")
        
        return headers
    
    def _handle_response_error(
        self,
        error: Exception,
        operation: str = "API request"
    ) -> Dict[str, Any]:
        """
        Handle common HTTP errors and convert to standardized response.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation for logging
            
        Returns:
            Standardized error response dictionary
        """
        if isinstance(error, httpx.HTTPStatusError):
            error_code = f"HTTP_{error.response.status_code}"
            error_description = f"HTTP {error.response.status_code}: {error.response.text}"
            status_code = error.response.status_code
            
            logger.error(
                f"HTTP error during {operation} - "
                f"Code: {error_code}, Status: {status_code}, "
                f"Response: {error.response.text}"
            )
            
            return {
                "success": False,
                "error_code": error_code,
                "error_description": error_description,
                "status_code": status_code
            }
        
        elif isinstance(error, httpx.TimeoutException):
            error_code = "TIMEOUT_ERROR"
            error_description = f"Request timeout after {self.timeout}s: {str(error)}"
            
            logger.error(f"Timeout error during {operation} - {error_description}")
            
            return {
                "success": False,
                "error_code": error_code,
                "error_description": error_description
            }
        
        elif isinstance(error, httpx.RequestError):
            error_code = "REQUEST_ERROR"
            error_description = f"Network/connection error: {str(error)}"
            
            logger.error(f"Request error during {operation} - {error_description}")
            
            return {
                "success": False,
                "error_code": error_code,
                "error_description": error_description
            }
        
        else:
            error_code = "UNEXPECTED_ERROR"
            error_description = f"Unexpected error: {type(error).__name__} - {str(error)}"
            
            logger.error(f"Unexpected error during {operation} - {error_description}", exc_info=True)
            
            return {
                "success": False,
                "error_code": error_code,
                "error_description": error_description
            }
    
    def _create_client(self, timeout: Optional[float] = None) -> httpx.Client:
        """
        Create an httpx.Client with default settings.
        
        Args:
            timeout: Optional timeout override, uses self.timeout if not provided
            
        Returns:
            Configured httpx.Client instance
        """
        return httpx.Client(
            timeout=timeout or self.timeout,
            verify=self.verify_ssl
        )

"""
Example: Using APIClient Base Class for Custom APIs

This example demonstrates how to use the reusable APIClient base class
from faciliter-lib to create authenticated API clients for any service.

The APIClient provides:
- Time-based HMAC authentication
- Legacy API key authentication
- Automatic header generation
- Standardized error handling
- SSL verification control
"""

from faciliter_lib.api_utils import APIClient
import httpx
from typing import Dict, Any, List, Optional


# ============================================================================
# Example 1: Simple API Client
# ============================================================================

class WeatherAPIClient(APIClient):
    """Example: Simple weather API client with authentication."""
    
    def get_forecast(self, city: str) -> Dict[str, Any]:
        """Get weather forecast for a city."""
        try:
            headers = self._prepare_headers()
            
            with self._create_client() as client:
                response = client.get(
                    f"{self.base_url}/forecast",
                    params={"city": city},
                    headers=headers
                )
                response.raise_for_status()
                return {
                    "success": True,
                    "data": response.json()
                }
        except Exception as e:
            return self._handle_response_error(e, operation=f"getting forecast for {city}")


# ============================================================================
# Example 2: API Client with Multiple Endpoints
# ============================================================================

class UserManagementAPIClient(APIClient):
    """Example: User management API with CRUD operations."""
    
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
    
    def list_users(self, limit: int = 100) -> Dict[str, Any]:
        """List all users."""
        try:
            headers = self._prepare_headers()
            
            with self._create_client() as client:
                response = client.get(
                    f"{self.base_url}/users",
                    params={"limit": limit},
                    headers=headers
                )
                response.raise_for_status()
                return {
                    "success": True,
                    "data": response.json()
                }
        except Exception as e:
            return self._handle_response_error(e, operation="listing users")


# ============================================================================
# Example 3: Using with Environment-Based Configuration
# ============================================================================

def create_api_client_from_env(api_name: str = "MY_API") -> APIClient:
    """
    Create an API client from environment variables with a custom prefix.
    
    Environment variables expected:
    - {API_NAME}_URL: Base URL
    - {API_NAME}_KEY: Legacy API key (optional)
    - {API_NAME}_AUTH_ENABLED: Enable time-based auth
    - {API_NAME}_AUTH_PRIVATE_KEY: Private key for time-based auth
    - {API_NAME}_AUTH_HEADER_NAME: Custom header name (optional)
    
    Example for KB API:
    - KB_API_URL=http://localhost:9095
    - KB_API_AUTH_ENABLED=true
    - KB_API_AUTH_PRIVATE_KEY=secret-key
    """
    import os
    
    base_url = os.getenv(f"{api_name}_URL")
    api_key = os.getenv(f"{api_name}_KEY")
    auth_enabled = os.getenv(f"{api_name}_AUTH_ENABLED", "false").lower() == "true"
    auth_private_key = os.getenv(f"{api_name}_AUTH_PRIVATE_KEY")
    auth_header_name = os.getenv(f"{api_name}_AUTH_HEADER_NAME", "x-auth-key")
    
    if not base_url:
        raise ValueError(f"Environment variable {api_name}_URL is required")
    
    return APIClient(
        base_url=base_url,
        api_key=api_key,
        auth_enabled=auth_enabled,
        auth_private_key=auth_private_key,
        auth_header_name=auth_header_name
    )


# ============================================================================
# Example 4: Custom Headers and Skip Auth
# ============================================================================

class CustomHeadersAPIClient(APIClient):
    """Example: API client with custom headers and conditional auth."""
    
    def public_endpoint(self) -> Dict[str, Any]:
        """Call a public endpoint without authentication."""
        try:
            # Skip authentication for public endpoints
            headers = self._prepare_headers(skip_auth=True)
            
            with self._create_client() as client:
                response = client.get(
                    f"{self.base_url}/public/status",
                    headers=headers
                )
                response.raise_for_status()
                return {
                    "success": True,
                    "data": response.json()
                }
        except Exception as e:
            return self._handle_response_error(e, operation="calling public endpoint")
    
    def private_endpoint_with_custom_headers(self, correlation_id: str) -> Dict[str, Any]:
        """Call a private endpoint with custom headers."""
        try:
            # Add custom headers in addition to authentication
            additional_headers = {
                "X-Correlation-ID": correlation_id,
                "X-Client-Version": "1.0.0"
            }
            headers = self._prepare_headers(additional_headers=additional_headers)
            
            with self._create_client() as client:
                response = client.get(
                    f"{self.base_url}/private/data",
                    headers=headers
                )
                response.raise_for_status()
                return {
                    "success": True,
                    "data": response.json()
                }
        except Exception as e:
            return self._handle_response_error(e, operation="calling private endpoint")


# ============================================================================
# Usage Examples
# ============================================================================

def main():
    print("=" * 80)
    print("APIClient Base Class Examples")
    print("=" * 80)
    
    # Example 1: Simple API with time-based auth
    print("\n1. Weather API with Time-Based Authentication")
    print("-" * 80)
    weather_client = WeatherAPIClient(
        base_url="https://api.weather.example.com",
        auth_enabled=True,
        auth_private_key="my-secret-weather-api-key-16chars"
    )
    print(f"✓ Weather API client initialized")
    print(f"  Auth method: {weather_client._get_auth_method()}")
    
    # Example 2: API with legacy API key
    print("\n2. User Management API with Legacy API Key")
    print("-" * 80)
    user_client = UserManagementAPIClient(
        base_url="https://api.users.example.com",
        api_key="legacy-api-key-12345"
    )
    print(f"✓ User Management API client initialized")
    print(f"  Auth method: {user_client._get_auth_method()}")
    
    # Example 3: No authentication
    print("\n3. Public API without Authentication")
    print("-" * 80)
    public_client = APIClient(
        base_url="https://api.public.example.com"
    )
    print(f"✓ Public API client initialized")
    print(f"  Auth method: {public_client._get_auth_method()}")
    
    # Example 4: Custom header name
    print("\n4. API with Custom Auth Header")
    print("-" * 80)
    custom_client = APIClient(
        base_url="https://api.custom.example.com",
        auth_enabled=True,
        auth_private_key="custom-secret-key-16-chars",
        auth_header_name="X-Custom-Auth-Token"
    )
    print(f"✓ Custom API client initialized")
    print(f"  Auth header: {custom_client.auth_header_name}")
    
    # Example 5: From environment variables
    print("\n5. API Client from Environment Variables")
    print("-" * 80)
    print("Set these environment variables:")
    print("  KB_API_URL=http://localhost:9095")
    print("  KB_API_AUTH_ENABLED=true")
    print("  KB_API_AUTH_PRIVATE_KEY=your-secret-key")
    print("\nThen use: create_api_client_from_env('KB_API')")
    
    # Example 6: Prepare headers
    print("\n6. Header Generation Examples")
    print("-" * 80)
    auth_client = APIClient(
        base_url="https://api.example.com",
        auth_enabled=True,
        auth_private_key="example-key-16-chars"
    )
    
    # With authentication
    headers_with_auth = auth_client._prepare_headers()
    print("Headers with auth:")
    for key, value in headers_with_auth.items():
        if key == "x-auth-key":
            print(f"  {key}: {value[:16]}... (64 chars total)")
        else:
            print(f"  {key}: {value}")
    
    # Without authentication (skip_auth=True)
    headers_no_auth = auth_client._prepare_headers(skip_auth=True)
    print("\nHeaders without auth:")
    for key, value in headers_no_auth.items():
        print(f"  {key}: {value}")
    
    # With custom headers
    custom_headers = {"X-Request-ID": "12345"}
    headers_with_custom = auth_client._prepare_headers(additional_headers=custom_headers)
    print("\nHeaders with custom additions:")
    for key, value in headers_with_custom.items():
        if key == "x-auth-key":
            print(f"  {key}: {value[:16]}... (64 chars total)")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("✓ All examples completed successfully!")
    print("=" * 80)
    
    print("\n💡 Key Takeaways:")
    print("  • Inherit from APIClient for any HTTP API")
    print("  • Authentication is handled automatically")
    print("  • Use _prepare_headers() for request headers")
    print("  • Use _handle_response_error() for error handling")
    print("  • Use _create_client() for httpx.Client instances")
    print("  • Support for time-based auth, API keys, or no auth")
    print("  • Environment-based configuration with custom prefixes")


if __name__ == "__main__":
    main()

"""Observability metadata models and documentation.

This module defines the structure and documentation for observability metadata
passed via the `from_` parameter in API requests.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

# Type alias for from_ parameter
FromMetadata = Optional[Union[str, Dict[str, Any]]]

# Centralized description for 'from' parameter used across applications for traceability
FROM_FIELD_DESCRIPTION = """Source information for observability and tracing (dict or JSON string).

Accepts either a JSON string or a dictionary with the following structure:
- session_id: Session identifier
- app_name: Application name (e.g., "Faciliter AI Platform")
- app_version: Application version (e.g., "0.1.0")
- model_name: AI model name (e.g., "gemini-2.5-flash")
- user_name: User's display name
- user_id: User's unique identifier (UUID)
- company_name: Organization name
- company_id: Organization unique identifier (UUID)

Example:
```json
{
    "session_id": "12",
    "app_name": "Faciliter AI Platform",
    "app_version": "0.1.0",
    "model_name": "gemini-2.5-flash",
    "user_name": "Sarah Mitchell",
    "user_id": "10000000-0000-0000-0000-000000000101",
    "company_name": "TechVision Solutions",
    "company_id": "10000000-0000-0000-0000-000000000001"
}
```

All fields are optional."""


class FromMetadataSchema(BaseModel):
    """Schema defining the expected structure of the `from_` metadata.
    
    The `from_` parameter provides contextual information for observability,
    tracing, and audit trails. It can be passed as either:
    - A JSON string (automatically parsed by FastAPI)
    - A dictionary object
    
    All fields are optional, but providing complete information enables
    better tracing and analytics.
    
    Example JSON string format:
    ```json
    {
        "session_id": "12",
        "app_name": "Faciliter AI Platform",
        "app_version": "0.1.0",
        "model_name": "gemini-2.5-flash",
        "user_name": "Sarah Mitchell",
        "user_id": "10000000-0000-0000-0000-000000000101",
        "company_name": "TechVision Solutions",
        "company_id": "10000000-0000-0000-0000-000000000001"
    }
    ```
    
    Example Python dict format:
    ```python
    {
        "session_id": "12",
        "app_name": "Faciliter AI Platform",
        "app_version": "0.1.0",
        "model_name": "gemini-2.5-flash",
        "user_name": "Sarah Mitchell",
        "user_id": "10000000-0000-0000-0000-000000000101",
        "company_name": "TechVision Solutions",
        "company_id": "10000000-0000-0000-0000-000000000001"
    }
    ```
    
    Fields:
        session_id: Unique identifier for the current session/conversation
        app_name: Name of the calling application
        app_version: Version of the calling application
        model_name: AI model being used (e.g., "gemini-2.5-flash", "gpt-4")
        user_name: Human-readable name of the user making the request
        user_id: Unique identifier for the user (UUID format recommended)
        company_name: Human-readable name of the organization
        company_id: Unique identifier for the organization (UUID format)
    """
    
    # Session context
    session_id: Optional[str] = Field(
        None,
        description="Unique identifier for the current session/conversation"
    )
    
    # Application context
    app_name: Optional[str] = Field(
        None,
        description="Name of the calling application"
    )
    app_version: Optional[str] = Field(
        None,
        description="Version of the calling application"
    )
    
    # Model context
    model_name: Optional[str] = Field(
        None,
        description="AI model being used (e.g., 'gemini-2.5-flash', 'gpt-4')"
    )
    
    # User context
    user_name: Optional[str] = Field(
        None,
        description="Human-readable name of the user making the request"
    )
    user_id: Optional[str] = Field(
        None,
        description="Unique identifier for the user (UUID format recommended)"
    )
    
    # Organization context
    company_name: Optional[str] = Field(
        None,
        description="Human-readable name of the organization"
    )
    company_id: Optional[str] = Field(
        None,
        description="Unique identifier for the organization (UUID format)"
    )


# Re-export FROM_FIELD_DESCRIPTION for backward compatibility
__all__ = ["FromMetadata", "FromMetadataSchema", "FROM_FIELD_DESCRIPTION"]

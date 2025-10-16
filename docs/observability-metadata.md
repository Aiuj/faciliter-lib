# Observability Metadata (`from_` Parameter)

This document describes the format and usage of the `from_` parameter used across all API endpoints for observability, tracing, and audit trails.

## Overview

The `from_` parameter provides contextual information about the source of an API request. This metadata is captured for:

- Distributed tracing and debugging
- User analytics and usage patterns
- Audit trails and compliance
- Performance monitoring across clients
- Session tracking for multi-turn interactions

## Parameter Format

The `from_` parameter accepts two formats:

### 1. JSON String

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

### 2. Python Dictionary

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

## Field Descriptions

All fields are **optional**, but providing complete information enables better observability.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `session_id` | string | Unique identifier for the current session/conversation | `"12"`, `"session-abc-123"` |
| `app_name` | string | Name of the calling application | `"Faciliter AI Platform"`, `"MyApp"` |
| `app_version` | string | Version of the calling application | `"0.1.0"`, `"1.2.3"` |
| `model_name` | string | AI model being used by the client | `"gemini-2.5-flash"`, `"gpt-4"` |
| `user_name` | string | Human-readable name of the user | `"Sarah Mitchell"`, `"John Doe"` |
| `user_id` | string | Unique identifier for the user (UUID recommended) | `"10000000-0000-0000-0000-000000000101"` |
| `company_name` | string | Human-readable name of the organization | `"TechVision Solutions"`, `"Acme Corp"` |
| `company_id` | string | Unique identifier for the organization (UUID) | `"10000000-0000-0000-0000-000000000001"` |

## Usage Examples

### FastAPI/HTTP Request

```bash
# Using JSON string in POST request
curl -X POST "https://api.example.com/v1/answer/question" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are your business hours?",
    "company_id": "10000000-0000-0000-0000-000000000001",
    "from": "{\"session_id\": \"12\", \"app_name\": \"Faciliter AI Platform\", \"app_version\": \"0.1.0\", \"model_name\": \"gemini-2.5-flash\", \"user_name\": \"Sarah Mitchell\", \"user_id\": \"10000000-0000-0000-0000-000000000101\", \"company_name\": \"TechVision Solutions\", \"company_id\": \"10000000-0000-0000-0000-000000000001\"}"
  }'
```

### Python Client

```python
import requests

# Using dictionary (automatically serialized by requests)
response = requests.post(
    "https://api.example.com/v1/answer/question",
    json={
        "query": "What are your business hours?",
        "company_id": "10000000-0000-0000-0000-000000000001",
        "from": {
            "session_id": "12",
            "app_name": "Faciliter AI Platform",
            "app_version": "0.1.0",
            "model_name": "gemini-2.5-flash",
            "user_name": "Sarah Mitchell",
            "user_id": "10000000-0000-0000-0000-000000000101",
            "company_name": "TechVision Solutions",
            "company_id": "10000000-0000-0000-0000-000000000001"
        }
    }
)
```

### MCP Client

```python
from mcp import ClientSession

# Using dictionary format
result = await session.call_tool(
    "answer_rfp_question",
    arguments={
        "query": "What are your business hours?",
        "company_id": "10000000-0000-0000-0000-000000000001",
        "from_": {
            "session_id": "12",
            "app_name": "Faciliter AI Platform",
            "app_version": "0.1.0",
            "model_name": "gemini-2.5-flash",
            "user_name": "Sarah Mitchell",
            "user_id": "10000000-0000-0000-0000-000000000101",
            "company_name": "TechVision Solutions",
            "company_id": "10000000-0000-0000-0000-000000000001"
        }
    }
)
```

## Best Practices

### 1. Session Tracking

For multi-turn conversations, maintain a consistent `session_id` across all related requests:

```python
import uuid

# Generate once per conversation
session_id = str(uuid.uuid4())

# Use in all related requests
for question in questions:
    response = await client.answer_question(
        query=question,
        company_id=company_id,
        from_={
            "session_id": session_id,  # Same for all questions in this conversation
            "app_name": "MyApp",
            "user_id": user_id
        }
    )
```

### 2. Version Tracking

Always include `app_version` to track behavior across client versions:

```python
from_metadata = {
    "app_name": "Faciliter AI Platform",
    "app_version": "0.1.0",  # Track version for analytics
    "user_id": user_id
}
```

### 3. User Context

Include both `user_id` and `user_name` for comprehensive audit trails:

```python
from_metadata = {
    "user_id": "10000000-0000-0000-0000-000000000101",  # For machine processing
    "user_name": "Sarah Mitchell",  # For human-readable logs
    "company_id": company_id
}
```

### 4. Model Tracking

Track which AI model your client is using for correlation with server-side model:

```python
from_metadata = {
    "model_name": "gemini-2.5-flash",  # Client-side model preference
    "app_name": "MyApp",
    "user_id": user_id
}
```

## Implementation Details

### Type Definition

```python
from typing import Any, Dict, Optional, Union

# Type alias
FromMetadata = Optional[Union[str, Dict[str, Any]]]
```

### Pydantic Model

```python
from pydantic import BaseModel, Field

class RequestModel(BaseModel):
    query: str
    company_id: str
    from_: FromMetadata = Field(
        None, 
        alias="from",  # Maps to 'from' in JSON
        description=FROM_FIELD_DESCRIPTION
    )
```

### Schema Definition

The complete schema is defined in `FromMetadataSchema` (see `api_utils/models/observability_models.py`):

```python
from api_utils.models import FromMetadataSchema

# Validate metadata
metadata = FromMetadataSchema(**from_data)
```

## API Documentation

When the FastAPI server generates OpenAPI documentation, the `from_` parameter will include the complete field descriptions and examples. Access the interactive documentation at:

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`
- **OpenAPI JSON**: `http://localhost:8080/openapi.json`

## Privacy and Security Considerations

### PII Handling

- `user_name` and `company_name` contain PII - handle according to privacy policies
- Consider anonymization for analytics
- Ensure GDPR/CCPA compliance when storing traces

### Data Minimization

Only include fields that are actively used for observability:

```python
# Minimal metadata (preferred for privacy)
from_metadata = {
    "session_id": session_id,
    "app_version": "0.1.0"
}

# Full metadata (use when audit trails are required)
from_metadata = {
    "session_id": session_id,
    "app_name": "MyApp",
    "app_version": "0.1.0",
    "user_id": user_id,
    "company_id": company_id
}
```

### Sensitive Data

**Never include** in `from_` metadata:

- ❌ Passwords or API keys
- ❌ Authentication tokens
- ❌ Payment information
- ❌ Personal health information
- ❌ Social security numbers

## Tracing Integration

The `from_` metadata is automatically integrated with the tracing system (Langfuse/OpenTelemetry):

```python
# Server-side (automatic)
tracing_client.add_metadata(metadata=from_)  # Captured for each request
```

View traces with full metadata in your observability platform.

## Related Documentation

- **API Models**: See `src/api_utils/models/observability_models.py`
- **Tracing**: See faciliter-lib tracing documentation
- **FastAPI Integration**: See `src/fastapi_server.py`
- **MCP Integration**: See `src/api_utils/mcp_endpoints.py`

## Support

For questions or issues:

1. Check OpenAPI documentation at `/docs`
2. Review this document
3. Contact the development team

# FROM_FIELD_DESCRIPTION Constant

## Overview

The `FROM_FIELD_DESCRIPTION` constant provides standardized documentation for the `from` parameter used across FastAPI applications for observability and tracing.

## Location

```python
from faciliter_lib import FROM_FIELD_DESCRIPTION
# or
from faciliter_lib.tracing import FROM_FIELD_DESCRIPTION
```

## Purpose

This constant ensures consistent documentation and usage patterns for the `from` parameter across all applications that use faciliter-lib for tracing and observability.

## Usage in FastAPI

```python
from fastapi import FastAPI, Query
from faciliter_lib import FROM_FIELD_DESCRIPTION, setup_tracing

app = FastAPI()
tracing_client = setup_tracing(name="my-app")

@app.post("/v1/some-endpoint")
async def some_endpoint(
    from_: Optional[str] = Query(None, alias="from", description=FROM_FIELD_DESCRIPTION)
):
    # Add metadata for tracing
    tracing_client.add_metadata(metadata=from_)
    
    # Your endpoint logic here
    pass
```

## Expected Format

The `from` parameter can be either:
- A JSON string
- A dictionary/object

### Structure

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

### Fields

All fields are optional:

- **session_id**: Unique identifier for the current session/conversation
- **app_name**: Name of the calling application
- **app_version**: Version of the calling application
- **model_name**: AI model being used (e.g., "gemini-2.5-flash", "gpt-4")
- **user_name**: Human-readable name of the user making the request
- **user_id**: Unique identifier for the user (UUID format recommended)
- **company_name**: Human-readable name of the organization
- **company_id**: Unique identifier for the organization (UUID format)

## Benefits

1. **Consistency**: All applications using faciliter-lib have the same documentation
2. **Centralized**: Single source of truth for the parameter description
3. **Versioned**: Changes are tracked in the library version
4. **Reusable**: Import once and use across all endpoints

## Migration from Local Definitions

If you have local definitions of `FROM_FIELD_DESCRIPTION`, replace:

```python
# Before
from api_utils.models import FROM_FIELD_DESCRIPTION

# After
from faciliter_lib import FROM_FIELD_DESCRIPTION
```

## Related

- See `faciliter_lib.tracing.TracingManager` for tracing client usage
- See `faciliter_lib.tracing.setup_tracing()` for initialization

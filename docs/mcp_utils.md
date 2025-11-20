"""  
mcp_utils.py - Utility functions for server stack

This module provides helper functions for command-line argument handling in server stack applications.

Functions:
    get_transport_from_args(): Checks command line args for --transport=... and returns the value if present.

**Note:** The `parse_from()` function has been moved to `core_lib.tracing.logging_context`. Import it from `core_lib.tracing` instead:

```python
from core_lib.tracing import parse_from
```

Example usage:
    from core_lib.mcp_utils import get_transport_from_args
    transport = get_transport_from_args()
"""
"""  
mcp_utils.py - Utility functions for Faciliter stack

This module provides helper functions for command-line argument handling in Faciliter stack applications.

Functions:
    get_transport_from_args(): Checks command line args for --transport=... and returns the value if present.

**Note:** The `parse_from()` function has been moved to `faciliter_lib.tracing.logging_context`. Import it from `faciliter_lib.tracing` instead:

```python
from faciliter_lib.tracing import parse_from
```

Example usage:
    from faciliter_lib.mcp_utils import get_transport_from_args
    transport = get_transport_from_args()
"""
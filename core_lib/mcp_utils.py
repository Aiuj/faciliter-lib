"""MCP (Model Context Protocol) utility functions.

This module provides utilities for MCP server configuration and setup.
"""
import sys


def get_transport_from_args():
    """Check command line args for --transport=... and return the value if present, else None."""
    for arg in sys.argv[1:]:
        if arg.startswith("--transport="):
            value = arg.split("=", 1)[1].strip().lower()
            if value in {"stdio", "sse", "http", "streamable-http"}:
                return value
            else:
                print(f"Invalid transport: {value}. Must be one of stdio, sse, streamable-http.")
                sys.exit(1)
    return None


"""
mcp_utils.py - Utility functions for Faciliter stack

This module provides helper functions for parsing and command-line argument handling in Faciliter stack applications.

Functions:
    parse_from(from_): Parses a JSON string or dict into a dict, returns empty dict on failure.
    get_transport_from_args(): Checks command line args for --transport=... and returns the value if present.

Example usage:
    from faciliter_utils.mcp_utils import parse_from, get_transport_from_args
    d = parse_from('{"foo": 1}')
    transport = get_transport_from_args()
"""

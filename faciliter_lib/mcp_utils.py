import sys

def parse_from(from_: str|dict) -> dict:
    """
    Parse the 'from_' JSON string into a dictionary.
    Returns an empty dict if parsing fails.
    """
    from_dict = None
    if from_:
        try:
            if isinstance(from_, str):
                # If from_ is a string, try to parse it as JSON
                import json
                from_dict = json.loads(from_)
            elif isinstance(from_, dict):
                # If from_ is already a dict, use it directly
                from_dict = from_
            else:
                raise ValueError("from_ must be a JSON string or a dictionary.")
        except Exception:
            from_dict = None
    return from_dict or {}

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


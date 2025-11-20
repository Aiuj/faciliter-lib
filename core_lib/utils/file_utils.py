"""Small utilities for writing incoming file content to temporary files.

These helpers centralize creation of temporary files from bytes, base64 strings,
or file-like objects so caller code doesn't repeat tempfile boilerplate.
"""
from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path
from typing import Optional, IO
from core_lib import get_module_logger

# Get module-specific logger
logger = get_module_logger()


def create_tempfile(file=None, file_content: str = None, filename: str = None, suffix: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """Create or resolve a temporary file path from various inputs.

    This helper centralizes tempfile creation and selection. Exactly one of the
    following should be provided:
      - file: a binary file-like object whose contents will be written to a temp file
      - file_content: a base64-encoded string which will be decoded and written to a temp file
      - filename: an existing filename to use directly (no file creation performed)

    Args:
        file: Optional file-like object opened in binary mode.
        file_content: Optional base64-encoded file contents as a string.
        filename: Optional path to an existing file to use as-is.
        suffix: Optional filename suffix for created temp files (e.g. '.xlsx').
        prefix: Optional filename prefix for created temp files.

    Returns:
        Absolute path (string) to the created temporary file or the provided filename.

    Raises:
        ValueError: If none of file, file_content, or filename are provided.
    """
    # Determine file path using centralized helpers
    temp_path = None
    if file is not None:
        logger.debug("Processing file object - creating temporary file")
        temp_path = save_fileobj_to_tempfile(file, suffix=suffix, prefix=prefix)
    elif file_content is not None:
        logger.debug("Processing base64 file content - creating temporary file")
        temp_path = save_base64_to_tempfile(file_content, suffix=suffix, prefix=prefix)
    elif filename is not None:
        logger.debug(f"Using provided filename: {filename}")
        temp_path = filename
    else:
        logger.error("No valid file input provided")
        raise ValueError("No valid file input provided.")
    return temp_path

def remove_tempfile(temp_path: str):
    """Remove a temporary file if it exists.

    Safely attempts to delete the given path and logs success or failure.
    Non-fatal: failures are logged as warnings but not raised.

    Args:
        temp_path: Path to the temporary file to remove.

    Notes:
        - Verifies path existence before attempting removal.
        - Any exception during os.remove is caught and logged as a warning.
    """
    if temp_path and Path(temp_path).exists():
        try:
            os.remove(temp_path)
            logger.debug(f"Temporary file cleaned up: {temp_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {temp_path}: {str(e)}")


def save_bytes_to_tempfile(content: bytes, suffix: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """Write bytes to a temporary file and return the absolute path.

    Args:
        content: Raw bytes to write.
        suffix: Optional filename suffix (e.g. '.xlsx').
        prefix: Optional filename prefix.

    Returns:
        Absolute path to the created temporary file as a string.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix or '', prefix=prefix or '')
    try:
        tmp.write(content)
        tmp.flush()
        return str(Path(tmp.name).resolve())
    finally:
        try:
            tmp.close()
        except Exception:
            pass


def save_base64_to_tempfile(b64_content: str, suffix: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """Decode a base64 string and write to a temporary file.

    Args:
        b64_content: Base64-encoded string.
        suffix: Optional filename suffix.
        prefix: Optional filename prefix.

    Returns:
        Absolute path to the created temporary file as a string.
    """
    raw = base64.b64decode(b64_content)
    return save_bytes_to_tempfile(raw, suffix=suffix, prefix=prefix)


def save_fileobj_to_tempfile(fileobj: IO[bytes], suffix: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """Read a binary file-like object and write its contents to a temporary file.

    Args:
        fileobj: File-like object opened in binary mode or exposing .read() returning bytes.
        suffix: Optional filename suffix.
        prefix: Optional filename prefix.

    Returns:
        Absolute path to the created temporary file as a string.
    """
    content = fileobj.read()
    return save_bytes_to_tempfile(content, suffix=suffix, prefix=prefix)

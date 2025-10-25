"""File logging handler with rotation support.

This module provides utilities for configuring file-based logging
with automatic rotation. Only imported when file logging is enabled.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def create_file_handler(
    file_path: str,
    level: int,
    max_bytes: int = 1_048_576,
    backup_count: int = 3,
) -> Optional[RotatingFileHandler]:
    """Create a rotating file handler for logging.
    
    Args:
        file_path: Path to the log file
        level: Logging level (e.g., logging.INFO)
        max_bytes: Maximum file size before rotation (default: 1 MB)
        backup_count: Number of backup files to keep (default: 3)
        
    Returns:
        RotatingFileHandler instance or None on failure
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        return file_handler
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Failed to create file handler at {file_path}: {e}"
        )
        return None

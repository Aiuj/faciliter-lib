"""
Centralized logging configuration for the MCP News application.
This module provides a consistent logger setup that should be used across all modules.
"""

import logging
import sys
import os
from typing import Optional, Union


# Global logger instance
_logger_initialized = False
_root_logger = None


def setup_logging(app_name: str = "faciliter_lib", name: Optional[str] = None, level: Optional[Union[str, int]] = None) -> logging.Logger:
    """
    Set up centralized logging configuration and return a logger instance.
    
    Args:
        app_name (str): Name of the application.
        name (str, optional): Name for the logger. If None, uses the calling module's __name__.
        level (str or int, optional): Logging level, can be string name or integer constant.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger_initialized, _root_logger
    
    # Initialize root logger only once. If `level` is not provided, consult
    # the `LOG_LEVEL` environment variable (defaults to INFO).
    if level is None:
        level_env = os.getenv("LOG_LEVEL", "INFO")
        level = level_env

    # Convert level to integer if it's a string
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    elif isinstance(level, int):
        numeric_level = level
    else:
        numeric_level = logging.INFO

    if not _logger_initialized:
        # Clear any existing handlers to avoid duplicates
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Set up the root logger configuration
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

        # Set specific logger levels to reduce noise
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("opensearch").setLevel(logging.WARNING)
        logging.getLogger("psycopg2").setLevel(logging.WARNING)
        logging.getLogger("redis").setLevel(logging.WARNING)

        _root_logger = logging.getLogger(app_name)
        _root_logger.setLevel(numeric_level)
        _logger_initialized = True

        _root_logger.info(f"Logging initialized with level: {numeric_level}")
    
    # Return a logger for the specific module
    if name is None:
        # Try to get the caller's module name
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "unknown")

    # Create module-specific logger as child of root logger
    logger = logging.getLogger(f"{app_name}.{name.split('.')[-1]}")
    logger.setLevel(numeric_level)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger for `name` without forcing global config initialization.

    If you want to (re)configure global logging, call `setup_logging()` from
    your application startup path. `get_logger` is a lightweight helper that
    simply returns a namespaced logger.
    """
    if name is None:
        return logging.getLogger("faciliter_lib")
    return logging.getLogger(name)


# Convenience function for getting logger with caller's name
def get_module_logger() -> logging.Logger:
    """Return a logger for the calling module without side-effects.

    This avoids initializing global logging during module import; call
    `setup_logging()` explicitly from application startup to configure
    handlers and levels.
    """
    import inspect

    frame = inspect.currentframe().f_back
    module_name = frame.f_globals.get("__name__", "unknown")
    return logging.getLogger(module_name)

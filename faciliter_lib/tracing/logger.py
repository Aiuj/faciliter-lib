"""
Centralized logging configuration for the MCP News application.
This module provides a consistent logger setup that should be used across all modules.
"""

import logging
import sys
from typing import Optional, Union


# Global logger instance
_logger_initialized = False
_root_logger = None


def setup_logging(name: Optional[str] = None, level: Optional[Union[str, int]] = logging.DEBUG) -> logging.Logger:
    """
    Set up centralized logging configuration and return a logger instance.
    
    Args:
        name (str, optional): Name for the logger. If None, uses the calling module's __name__.
        level (str or int, optional): Logging level, can be string name or integer constant.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger_initialized, _root_logger
    
    # Initialize root logger only once
    if not _logger_initialized:
        # Clear any existing handlers to avoid duplicates
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Convert level to integer if it's a string
        if isinstance(level, str):
            numeric_level = getattr(logging, level.upper(), logging.DEBUG)
        else:
            numeric_level = level
            
        # Set up the root logger configuration
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        
        _root_logger = logging.getLogger("mcp_news")
        _root_logger.setLevel(numeric_level)
        _logger_initialized = True
        
        _root_logger.info(f"Logging initialized with level: {level}")
    
    # Return a logger for the specific module
    if name is None:
        # Try to get the caller's module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    # Convert level to integer if it's a string
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.DEBUG)
    else:
        numeric_level = level
    
    # Create module-specific logger as child of root logger
    logger = logging.getLogger(f"mcp_news.{name.split('.')[-1]}")
    logger.setLevel(numeric_level)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. Alias for setup_logging for convenience.
    
    Args:
        name (str, optional): Name for the logger. If None, uses the calling module's __name__.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logging(name)


# Convenience function for getting logger with caller's name
def get_module_logger() -> logging.Logger:
    """
    Get a logger using the calling module's __name__.
    
    Returns:
        logging.Logger: Configured logger instance for the calling module
    """
    import inspect
    frame = inspect.currentframe().f_back
    module_name = frame.f_globals.get('__name__', 'unknown')
    return setup_logging(module_name)

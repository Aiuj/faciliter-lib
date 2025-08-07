# Centralized Logging Setup for MCP News

This document explains how the centralized logging system works in the MCP News application and how to use it consistently across all modules.

## Overview

The application now uses a centralized logging configuration through the `logger_config.py` module. This ensures that:

1. **All modules use the same logging format and configuration**
2. **Log levels are controlled centrally via environment variables**
3. **No duplicate logging setup across modules**
4. **Consistent naming convention for all loggers**

## How It Works

### Logger Configuration

The centralized logging system is managed by `src/logger_config.py`, which:

- Sets up a root logger named `mcp_news` 
- Creates module-specific child loggers (e.g., `mcp_news.main`, `mcp_news.utils`, etc.)
- Uses the `LOG_LEVEL` setting from `settings.py` (which reads from environment variables)
- Applies a consistent format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`

### Environment Configuration

The log level is controlled by the `LOG_LEVEL` environment variable in your `.env` file:

```bash
# Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
LOG_LEVEL=DEBUG
```

## Usage in Your Modules

### For New Modules

```python
# Import the centralized logger at the top of your module
from logger_config import get_module_logger

# Get a logger instance for your module
logger = get_module_logger()

# Use the logger throughout your module
def my_function():
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error message")
    logger.debug("This is a debug message (only shown if LOG_LEVEL=DEBUG)")
```

### For Existing Modules

Replace the old logging setup:

```python
# OLD WAY - Don't do this anymore
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

With the new centralized setup:

```python
# NEW WAY - Use this instead
from logger_config import get_module_logger
logger = get_module_logger()
```

## Key Benefits

### 1. Consistent Formatting
All log messages now follow the same format:
```
2025-08-06 18:25:41,076 [INFO] mcp_news.main: Starting application
2025-08-06 18:25:41,102 [DEBUG] mcp_news.utils: Processing date string
2025-08-06 18:25:41,115 [ERROR] mcp_news.gemini_provider: API call failed
```

### 2. Centralized Control
Change the log level once in your `.env` file and it affects the entire application:
- `LOG_LEVEL=DEBUG` - Shows all messages (very verbose)
- `LOG_LEVEL=INFO` - Shows info, warning, error, and critical messages
- `LOG_LEVEL=WARNING` - Shows only warnings, errors, and critical messages
- `LOG_LEVEL=ERROR` - Shows only errors and critical messages

### 3. Module Identification
Each log message clearly shows which module generated it:
- `mcp_news.main` - Messages from main.py
- `mcp_news.utils` - Messages from utils.py  
- `mcp_news.gemini_provider` - Messages from gemini_provider.py
- `mcp_news.tools.cache_manager` - Messages from tools/cache_manager.py

### 4. No Duplicate Setup
Previously, each module was setting up its own logging configuration, potentially conflicting with others. Now there's one central configuration.

## Modules Updated

The following modules have been updated to use centralized logging:

### Core Modules
- `src/main.py` - Main application entry point
- `src/utils.py` - Utility functions
- `src/article_reader.py` - Article reading functionality

### Provider Modules  
- `src/gemini_provider.py` - Google Gemini API integration
- `src/google_provider.py` - Google News provider
- `src/qwant_provider.py` - Qwant search provider  
- `src/rss_provider.py` - RSS feed processing

### Tool Modules
- `src/tools/cache_manager.py` - Redis caching
- `src/tools/crawl4ai_extraction.py` - Web crawling and extraction

## Testing the Setup

Run the test script to verify centralized logging is working:

```bash
python test_logging.py
```

This will demonstrate that all modules use the same logger configuration and formatting.

## Migration Notes

### What Changed
1. Removed individual `logging.basicConfig()` calls from each module
2. Replaced `import logging` and `logging.getLogger(__name__)` with centralized setup
3. Updated all `logging.info()`, `logging.warning()`, etc. calls to use `logger.info()`, `logger.warning()`, etc.

### What Stayed the Same
- All the actual logging calls in your code work exactly the same
- Log levels and message formatting remain consistent
- Environment-based configuration still works

### Troubleshooting

If you encounter issues:

1. **Import errors**: Make sure `logger_config.py` is in your Python path
2. **Missing logs**: Check your `LOG_LEVEL` environment variable
3. **Duplicate logs**: Remove any remaining `logging.basicConfig()` calls from individual modules

## Best Practices

1. **Always use the centralized logger**: Import from `logger_config` rather than setting up logging manually
2. **Use appropriate log levels**: 
   - `DEBUG` for detailed diagnostic information
   - `INFO` for general information about program execution
   - `WARNING` for unexpected situations that don't prevent the program from working
   - `ERROR` for serious problems that prevented a function from working
   - `CRITICAL` for very serious errors that might cause the program to terminate

3. **Include context in log messages**: Add relevant details that will help with debugging
4. **Don't log sensitive information**: Avoid logging passwords, API keys, or personal data

This centralized logging setup provides a much cleaner, more maintainable approach to logging across the entire MCP News application.

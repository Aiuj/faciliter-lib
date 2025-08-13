
# Centralized Logging in faciliter-lib

This document explains how to use the centralized logging system provided by `faciliter-lib` and how to apply it consistently across your codebase.


## Overview

`faciliter-lib` provides a centralized logging configuration in `faciliter_lib.tracing.logger`. This ensures:

1. **All modules can use a consistent logging format and configuration**
2. **Log levels can be controlled centrally**
3. **No duplicate logging setup across modules**
4. **Consistent naming convention for all loggers**


## How It Works

The centralized logging system is managed by `faciliter_lib.tracing.logger`:

- Sets up a root logger for your application
- Provides helper functions to get module-specific loggers
- Allows log level configuration (default: DEBUG)
- Applies a consistent format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`


### Log Level Configuration

You can set the log level by passing it to the logger setup functions, or by using environment variables in your application logic.


## Usage in Your Modules

### Recommended Usage

```python
# Import the centralized logger at the top of your module
from faciliter_lib.tracing.logger import get_module_logger

# Get a logger instance for your module
logger = get_module_logger()

# Use the logger throughout your module
def my_function():
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error message")
    logger.debug("This is a debug message")
```

### Alternative: Custom App Name or Level

```python
from faciliter_lib.tracing.logger import setup_logging
logger = setup_logging(app_name="my_app", level="INFO")
```


## Key Benefits

1. **Consistent Formatting**: All log messages follow the same format:
    ```
    2025-08-07 12:00:00,000 [INFO] my_app.module: Message
    ```
2. **Centralized Control**: Set the log level in one place for your whole app.
3. **Module Identification**: Each log message shows which module generated it.
4. **No Duplicate Setup**: Avoids conflicting logger configs across modules.


## Current Status

The centralized logger is available, but most modules in `faciliter-lib` currently use the standard `logging` module directly. For new code, use the centralized logger as shown above. Migrating existing modules to use it is recommended for consistency.


## Testing the Setup

You can test the logger in a Python shell:

```python
from faciliter_lib.tracing.logger import get_module_logger
logger = get_module_logger()
logger.info("Centralized logging works!")
```


## Migration Notes

### What to Change
1. Remove individual `logging.basicConfig()` calls from each module.
2. Replace `import logging` and `logging.getLogger(__name__)` with the centralized logger setup.
3. Update all `logging.info()`, `logging.warning()`, etc. calls to use your logger instance.

### Troubleshooting

1. **Import errors**: Make sure you import from `faciliter_lib.tracing.logger`.
2. **Missing logs**: Check your log level configuration.
3. **Duplicate logs**: Remove any remaining `logging.basicConfig()` calls from modules.


## Best Practices

1. **Always use the centralized logger**: Import from `faciliter_lib.tracing.logger` rather than setting up logging manually.
2. **Use appropriate log levels**: 
    - `DEBUG` for detailed diagnostic information
    - `INFO` for general information about program execution
    - `WARNING` for unexpected situations that don't prevent the program from working
    - `ERROR` for serious problems that prevented a function from working
    - `CRITICAL` for very serious errors that might cause the program to terminate
3. **Include context in log messages**: Add relevant details that will help with debugging.
4. **Don't log sensitive information**: Avoid logging passwords, API keys, or personal data.

This centralized logging setup provides a cleaner, more maintainable approach to logging across all code using `faciliter-lib`.

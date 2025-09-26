## Centralized Logging for faciliter-lib

This document explains the centralized logging utilities provided by `faciliter-lib` and how to use them consistently across applications, scripts, and libraries that depend on the package.

## Overview

The library exposes a centralized logging configuration via `faciliter_lib.tracing.logger` (re-exported from the top-level package). This provides:

1. Consistent logging format and handler setup (console + optional rotating file)
2. Centralized control of log levels via arguments, settings, or environment
3. Safe, side-effect free module log access (modules do not initialize global logging)
4. Ability to reconfigure logging later (e.g., promote INFO → DEBUG) using `force=True`
5. Optional rotating file logging with size-based rotation

## How It Works

### Logger Configuration

Managed by `faciliter_lib.tracing.logger`:

- Root logger named after `app_name` (optional). Resolution precedence:
    1. Explicit `app_name` argument
    2. `app_settings.app_name` if `app_settings` provided
    3. `APP_NAME` environment variable
    4. Fallback: `faciliter_lib`
- Module-specific loggers (e.g., `faciliter_lib.rate_limiter`)
- Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Optional rotating file handler
- Reconfiguration on demand

### Configuration Precedence

Log level precedence (highest → lowest):
1. Explicit `level` argument to `setup_logging`
2. `AppSettings.log_level` (when `app_settings` provided)
3. `LOG_LEVEL` environment variable
4. Default: `INFO`

File logging activation precedence:
1. Explicit `file_logging` argument
2. `LOG_FILE_ENABLED` environment variable (true/1/on/yes)
3. Default: disabled

### Environment Variables

```bash
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE_ENABLED=false      # Enable rotating file logging
LOG_FILE_PATH=logs/app.log  # Default: logs/<app_name>.log
LOG_FILE_MAX_BYTES=1048576  # 1 MB rotation threshold
LOG_FILE_BACKUP_COUNT=3     # Keep this many rotated archives
```

## Usage Patterns

### Application Entrypoint (API server / CLI main)

```python
from faciliter_lib import setup_logging
from faciliter_lib.config.app_settings import AppSettings

settings = AppSettings.from_env()
# app_name auto-resolves from settings; explicit arg not required
logger = setup_logging(app_settings=settings)
logger.info("Application startup complete")
```

Reconfigure with higher verbosity after CLI flag parsing:

```python
setup_logging(level="INFO")
# later after parsing --debug
setup_logging(level="DEBUG", force=True)
```

Enable file logging:

```python
setup_logging(level="INFO", file_logging=True, file_path="logs/service.log")
```

### Library / Internal Module Code

Avoid calling `setup_logging` inside library modules. Use lightweight accessors:

```python
from faciliter_lib import get_module_logger
logger = get_module_logger()

def compute():
    logger.debug("Running compute step")
```

Explicit naming:

```python
from faciliter_lib import get_logger
logger = get_logger("faciliter_lib.custom")
```

### Script-Level One-Off Override

```python
from faciliter_lib import setup_logging
log = setup_logging(level="DEBUG", file_logging=True, file_path="logs/debug_script.log")
log.debug("Verbose diagnostics enabled")
```

### Inspect Last Configuration

```python
from faciliter_lib import setup_logging, get_last_logging_config
setup_logging(level="INFO", file_logging=True)
print(get_last_logging_config())
```

## Key Benefits

### 1. Consistent Formatting
```
2025-09-26 10:03:12,431 [INFO] faciliter_lib.rate_limiter: Token bucket replenished
2025-09-26 10:03:12,432 [DEBUG] faciliter_lib.openai_provider: Request payload size=842 chars
```

### 2. Centralized, Reconfigurable Control
Precedence-based level selection with runtime `force=True` reconfiguration.

### 3. Clear Module Identification
Logger names reflect origin (e.g., `faciliter_lib.tools.excel_manager`).

### 4. No Duplicate Setup
Modules do not invoke `logging.basicConfig()`, preventing duplicate handlers.

### 5. Optional Rotating File Logging
Enable via flag or environment without changing module code.

## File Logging & Rotation

Uses `logging.handlers.RotatingFileHandler` with size-based rotation.

Examples:
```python
setup_logging(file_logging=True)  # logs/faciliter_lib.log
setup_logging(file_logging=True, file_path="/var/log/myapp/app.log", file_max_bytes=5_000_000, file_backup_count=10)
```

If file handler creation fails (permission / path), a warning is emitted and console logging continues.

## Migration Notes

### Recommended Practices
1. Only call `setup_logging` in your process entrypoint.
2. Use `get_module_logger()` inside library / module code.
3. Use `force=True` to reconfigure after initial setup if needed.
4. Prefer structured, contextual messages; avoid secrets (API keys, PII).

### Common Troubleshooting
1. Import errors: ensure `faciliter_lib` installed / in PYTHONPATH.
2. Missing logs: verify level precedence (explicit arg beats env).
3. Duplicate logs: multiple `setup_logging` calls without `force=True` or stray `basicConfig` calls.
4. No file output: ensure `LOG_FILE_ENABLED=true` or `file_logging=True` and that directory is writable.

## Best Practices Summary

Use log levels appropriately:
- DEBUG: detailed diagnostic data
- INFO: high-level application flow
- WARNING: unexpected but recoverable situations
- ERROR: failures of operations / requests
- CRITICAL: unrecoverable errors requiring immediate attention

Include contextual identifiers (ids, counts, durations) but exclude secrets and large payload bodies.

This centralized system delivers a clean, composable, and script‑friendly logging approach across all `faciliter-lib` components.

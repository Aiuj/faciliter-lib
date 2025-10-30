"""Centralized logging utilities for faciliter-lib.

Capabilities:
 - One-time global logging initialization that can be triggered from an application entrypoint
     (e.g. API server startup) using settings or environment variables.
 - Module-level lightweight accessors (`get_logger`, `get_module_logger`) that DO NOT force
     global initialization during import time.
 - Override support: callers can explicitly pass a `level` to `setup_logging` to override
     environment / settings derived values (useful for scripts or ad‑hoc notebooks).
 - Optional file logging with rotation (disabled by default) controlled via function params
     or environment variables.
 - Optional OVH Logs Data Platform integration via GELF protocol (lazy-loaded when enabled).
 - Optional OpenTelemetry Protocol (OTLP) integration for sending logs to OTLP collectors
     (lazy-loaded when enabled).

Environment variables (used only if explicit params not provided):
 LOG_LEVEL                -> root/application log level (default: INFO)
 LOG_FILE_ENABLED=true    -> enable file logging (default: false)
 LOG_FILE_PATH=logs/app.log
 LOG_FILE_MAX_BYTES=1048576 (1MB default) 
 LOG_FILE_BACKUP_COUNT=3
 OVH_LDP_ENABLED=true     -> enable OVH LDP integration (default: false)
 OVH_LDP_TOKEN            -> OVH LDP authentication token
 OVH_LDP_ENDPOINT         -> OVH LDP endpoint (e.g., gra1.logs.ovh.com)
 OTLP_ENABLED=true        -> enable OTLP integration (default: false)
 OTLP_ENDPOINT            -> OTLP collector endpoint (default: http://localhost:4318/v1/logs)
 OTLP_HEADERS             -> JSON string of HTTP headers

Notes:
 - Re-calling `setup_logging` with `force=True` allows reconfiguration (e.g. promote from
     default INFO to DEBUG after parsing CLI flags).
 - Handlers are loaded lazily - only imported when their features are enabled for better performance.
 - This module avoids importing application settings at import time to prevent circular imports;
     pass an `app_settings` or `logger_settings` object to `setup_logging` if you already loaded configuration.
"""

import logging
import sys
import os
from typing import Optional, Union, Any

try:  # Optional – settings may not be available yet
    from faciliter_lib.config.app_settings import AppSettings  # type: ignore
except Exception:  # pragma: no cover - defensive
    AppSettings = Any  # fallback typing only

try:
    from faciliter_lib.config.logger_settings import LoggerSettings  # type: ignore
except Exception:  # pragma: no cover - defensive
    LoggerSettings = Any  # fallback typing only


_logger_initialized = False
_root_logger: Optional[logging.Logger] = None

_LAST_CONFIG: dict = {}  # keep track of parameters used to configure logging


def _resolve_logger_name(app_name: str, module_name: Optional[str]) -> str:
    """Return a consistent logger name under the application's root namespace.

    Rules:
    - If module_name is None/empty, return app_name.
    - If module_name already starts with "{app_name}.", return module_name (avoid double-prefixing).
    - If module_name equals app_name, return app_name.
    - Otherwise, prefix with "{app_name}." preserving full module path (no truncation).
    """
    if not module_name:
        return app_name
    if module_name == app_name:
        return app_name
    prefix = f"{app_name}."
    if module_name.startswith(prefix):
        return module_name
    return f"{app_name}.{module_name}"


def setup_logging(
    app_name: Optional[str] = None,
    name: Optional[str] = None,
    level: Optional[Union[str, int]] = None,
    app_settings: Optional[Any] = None,
    logger_settings: Optional[Any] = None,
    *,
    file_logging: Optional[bool] = None,
    file_path: Optional[str] = None,
    file_max_bytes: Optional[int] = None,
    file_backup_count: Optional[int] = None,
    force: bool = False,
) -> logging.Logger:
    """Initialize (or reconfigure) global logging and return a module logger.

    Precedence for determining log level:
        explicit `level` arg > logger_settings.log_level > app_settings.log_level > LOG_LEVEL env > INFO

    File logging is enabled when (in precedence order):
        explicit `file_logging` arg True | logger_settings.file_logging | env LOG_FILE_ENABLED=true/1 | False
    
    OVH Logs Data Platform integration is enabled via logger_settings.ovh_ldp_enabled.

    Args:
        app_name: Root application logger namespace. If None, resolved by precedence:
                  explicit arg > app_settings.app_name > APP_NAME env > "faciliter_lib".
        name: Optional explicit module name (defaults to caller module).
        level: Override log level (str/int). Highest precedence.
        app_settings: Optional AppSettings instance (used for log level and environment detection).
        logger_settings: Optional LoggerSettings instance with file and OVH LDP configuration.
        file_logging: Explicitly enable/disable file logging (overrides env if not None).
        file_path: Path to log file (default derived: logs/<app_name>.log).
        file_max_bytes: Rotate at this size (default 1MB or env LOG_FILE_MAX_BYTES).
        file_backup_count: Number of rotated backups to keep (default 3 or env LOG_FILE_BACKUP_COUNT).
        force: If True, reconfigure even if already initialized.

    Returns:
        logging.Logger: A logger instance scoped to the caller / provided name.
    """
    global _logger_initialized, _root_logger, _LAST_CONFIG

    # Resolve application name
    if app_name is None:
        candidate = None
        if app_settings is not None:
            candidate = getattr(app_settings, "app_name", None)
        if not candidate:
            candidate = os.getenv("APP_NAME")
        app_name = candidate or "faciliter_lib"

    # Determine log level (precedence: level arg > logger_settings > app_settings > env)
    if level is None:
        if logger_settings is not None:
            level = getattr(logger_settings, "log_level", None)
        if level is None and app_settings is not None:
            level = getattr(app_settings, "log_level", None)
        if level is None:
            level = os.getenv("LOG_LEVEL", "INFO")

    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.INFO)
    elif isinstance(level, int):
        numeric_level = level
    else:
        numeric_level = logging.INFO

    # Determine file logging config (precedence: explicit args > logger_settings > env)
    if file_logging is None:
        if logger_settings is not None:
            file_logging = getattr(logger_settings, "file_logging", False)
        else:
            raw = os.getenv("LOG_FILE_ENABLED", "false").lower()
            file_logging = raw in {"1", "true", "yes", "on"}
    
    if file_path is None:
        if logger_settings is not None:
            file_path = getattr(logger_settings, "file_path", None)
        if file_path is None:
            file_path = os.getenv("LOG_FILE_PATH") or os.path.join("logs", f"{app_name}.log")
    
    if file_max_bytes is None:
        if logger_settings is not None:
            file_max_bytes = getattr(logger_settings, "file_max_bytes", 1_048_576)
        else:
            try:
                file_max_bytes = int(os.getenv("LOG_FILE_MAX_BYTES", "1048576"))
            except ValueError:
                file_max_bytes = 1_048_576
    
    if file_backup_count is None:
        if logger_settings is not None:
            file_backup_count = getattr(logger_settings, "file_backup_count", 3)
        else:
            try:
                file_backup_count = int(os.getenv("LOG_FILE_BACKUP_COUNT", "3"))
            except ValueError:
                file_backup_count = 3
    
    # Determine OVH LDP config from logger_settings
    ovh_ldp_enabled = False
    ovh_ldp_config = {}
    if logger_settings is not None:
        ovh_ldp_enabled = getattr(logger_settings, "ovh_ldp_enabled", False)
        if ovh_ldp_enabled:
            ovh_ldp_config = {
                "token": getattr(logger_settings, "ovh_ldp_token", None),
                "endpoint": getattr(logger_settings, "ovh_ldp_endpoint", None),
                "port": getattr(logger_settings, "ovh_ldp_port", 12202),
                "protocol": getattr(logger_settings, "ovh_ldp_protocol", "gelf_tcp"),
                "use_tls": getattr(logger_settings, "ovh_ldp_use_tls", True),
                "facility": getattr(logger_settings, "ovh_ldp_facility", "user"),
                "additional_fields": getattr(logger_settings, "ovh_ldp_additional_fields", {}),
                "timeout": getattr(logger_settings, "ovh_ldp_timeout", 10),
                "compress": getattr(logger_settings, "ovh_ldp_compress", True),
            }
    
    # Determine OTLP config from logger_settings
    otlp_enabled = False
    otlp_config = {}
    if logger_settings is not None:
        otlp_enabled = getattr(logger_settings, "otlp_enabled", False)
        if otlp_enabled:
            otlp_config = {
                "endpoint": getattr(logger_settings, "otlp_endpoint", "http://localhost:4318/v1/logs"),
                "headers": getattr(logger_settings, "otlp_headers", {}),
                "timeout": getattr(logger_settings, "otlp_timeout", 10),
                "insecure": getattr(logger_settings, "otlp_insecure", False),
                "service_name": getattr(logger_settings, "otlp_service_name", app_name),
                "service_version": getattr(logger_settings, "otlp_service_version", None),
                "log_level": getattr(logger_settings, "otlp_log_level", None),
            }

    new_config = {
        "level": numeric_level,
        "file_logging": file_logging,
        "file_path": file_path,
        "file_max_bytes": file_max_bytes,
        "file_backup_count": file_backup_count,
        "app_name": app_name,
        "ovh_ldp_enabled": ovh_ldp_enabled,
        "ovh_ldp_endpoint": ovh_ldp_config.get("endpoint") if ovh_ldp_enabled else None,
        "otlp_enabled": otlp_enabled,
        "otlp_endpoint": otlp_config.get("endpoint") if otlp_enabled else None,
        "otlp_log_level": otlp_config.get("log_level") if otlp_enabled else None,
    }

    if _logger_initialized and not force:
        # Already configured; just return module logger (still allow different module name)
        pass
    else:
        # If reconfiguring, clear existing handlers from root
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Console handler (always enabled)
        handlers = [logging.StreamHandler(sys.stdout)]
        
        # Add file handler if enabled (lazy import)
        if file_logging:
            try:
                from .handlers.file_handler import create_file_handler
                file_handler = create_file_handler(
                    file_path=file_path,
                    level=numeric_level,
                    max_bytes=file_max_bytes,
                    backup_count=file_backup_count,
                )
                if file_handler:
                    handlers.append(file_handler)
            except Exception as e:  # pragma: no cover (IO edge cases)
                logging.basicConfig()
                logging.getLogger(app_name).warning(f"Failed to set up file logging: {e}")
        
        # Add OVH LDP handler if enabled (lazy import)
        if ovh_ldp_enabled:
            try:
                protocol = ovh_ldp_config.get("protocol", "gelf_tcp").lower()
                if protocol == "gelf_tcp":
                    from .handlers.gelf_handler import GELFTCPHandler
                    ovh_handler = GELFTCPHandler(
                        host=ovh_ldp_config["endpoint"],
                        port=ovh_ldp_config["port"],
                        token=ovh_ldp_config["token"],
                        use_tls=ovh_ldp_config["use_tls"],
                        compress=ovh_ldp_config["compress"],
                        additional_fields=ovh_ldp_config["additional_fields"],
                        timeout=ovh_ldp_config["timeout"],
                    )
                    ovh_handler.setLevel(numeric_level)
                    handlers.append(ovh_handler)
                else:
                    # Log warning for unsupported protocols
                    logging.basicConfig()
                    logging.getLogger(app_name).warning(
                        f"OVH LDP protocol '{protocol}' not yet supported. Only gelf_tcp is currently implemented."
                    )
            except Exception as e:  # pragma: no cover (network edge cases)
                logging.basicConfig()
                logging.getLogger(app_name).warning(f"Failed to set up OVH LDP logging: {e}")
        
        # Add OTLP handler if enabled (lazy import)
        if otlp_enabled:
            try:
                from .handlers.otlp_handler import OTLPHandler
                otlp_handler = OTLPHandler(
                    endpoint=otlp_config["endpoint"],
                    headers=otlp_config["headers"],
                    timeout=otlp_config["timeout"],
                    insecure=otlp_config["insecure"],
                    service_name=otlp_config["service_name"],
                    service_version=otlp_config["service_version"],
                )
                # Use OTLP-specific log level if provided, otherwise use global level
                otlp_level_str = otlp_config.get("log_level") or level
                if isinstance(otlp_level_str, str):
                    otlp_numeric_level = getattr(logging, otlp_level_str.upper(), numeric_level)
                else:
                    otlp_numeric_level = numeric_level
                otlp_handler.setLevel(otlp_numeric_level)
                otlp_handler.start()  # Start background worker
                handlers.append(otlp_handler)
            except Exception as e:  # pragma: no cover (network edge cases)
                logging.basicConfig()
                logging.getLogger(app_name).warning(f"Failed to set up OTLP logging: {e}")

        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=handlers,
            force=True,  # Python 3.8+: replace handlers
        )
        # Install logging context filter for request tracing
        from .logging_context import install_logging_context_filter
        install_logging_context_filter()


        # Noise reduction
        for noisy in ["urllib3", "requests", "opensearch", "psycopg2", "redis"]:
            try:
                logging.getLogger(noisy).setLevel(logging.WARNING)
            except Exception:
                pass

        # Get the app logger - this is a child of root, inherits handlers via propagation
        _root_logger = logging.getLogger(app_name)
        # Do NOT set level on app logger - let it inherit from root or use NOTSET
        # Setting level here creates an additional filter that can block propagated logs
        _root_logger.setLevel(logging.NOTSET)  # NOTSET = inherit from parent (root)
        _logger_initialized = True
        _LAST_CONFIG = new_config
        _root_logger.info(
            "Logging initialized", extra={"config": {k: v for k, v in new_config.items() if k != "level"}, "level_int": numeric_level}
        )

    # Determine caller module name if not provided and resolve final logger name consistently
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "unknown")

    resolved_name = _resolve_logger_name(app_name, name)
    logger = logging.getLogger(resolved_name)
    # Do NOT set level on module loggers - let them inherit from parent chain
    # Setting level here creates an additional filter that blocks propagated logs
    logger.setLevel(logging.NOTSET)  # NOTSET = inherit effective level from parent
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
    
    The logger is namespaced under the app logger (if configured) to ensure
    proper handler inheritance, especially for OTLP and other remote handlers.
    """
    import inspect

    frame = inspect.currentframe().f_back
    module_name = frame.f_globals.get("__name__", "unknown")
    
    # If we have a configured root logger, namespace under it
    # This ensures all module loggers inherit handlers (OTLP, file, etc.)
    if _root_logger is not None:
        app_name = _root_logger.name
        # Create logger as child of app logger using consistent naming
        return logging.getLogger(_resolve_logger_name(app_name, module_name))
    
    # Fallback: return module logger directly (before setup_logging is called)
    return logging.getLogger(module_name)


def get_last_logging_config() -> dict:
    """Return the last applied logging configuration dictionary.

    Useful for debugging / tests.
    """
    return dict(_LAST_CONFIG)


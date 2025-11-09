"""Example Django WSGI configuration with faciliter-lib logging.

This example shows how to properly configure faciliter-lib logging in a Django
application with OTLP (OpenTelemetry) support and proper shutdown handling.

CRITICAL: You MUST add `LOGGING_CONFIG = None` to your settings.py file to disable
Django's default logging configuration. See the settings.py example below.

Usage:
    1. Add LOGGING_CONFIG = None to settings.py (REQUIRED)
    2. Set environment variables (see .env.example below)
    3. Run with Gunicorn: gunicorn myproject.wsgi:application
    4. Logs will be sent to console, file, and OTLP collector
"""

import os
import signal
import sys
from django.core.wsgi import get_wsgi_application
from faciliter_lib.config.logger_settings import LoggerSettings
from faciliter_lib.tracing.logger import setup_logging, flush_logging, get_module_logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# === Configure Logging ===
# Note: LOGGING_CONFIG = None MUST be set in settings.py
# Without this, Django will override faciliter-lib's logging configuration
# Load settings from environment variables
settings = LoggerSettings.from_env()

# Initialize logging (replaces Django's default LOGGING)
setup_logging(
    app_name="my-django-app",
    logger_settings=settings,
    force=True  # Override any existing configuration
)

logger = get_module_logger()
logger.info(
    "Django application starting",
    extra={
        "python_version": sys.version,
        "otlp_enabled": settings.otlp_enabled,
        "file_logging": settings.file_logging,
    }
)

# === Critical: Shutdown Handler for OTLP ===
# OTLP handler uses background thread that needs explicit flush
# Without this, logs may be lost on server shutdown
def handle_shutdown(signum, frame):
    """Flush OTLP logs before server shutdown"""
    signal_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
    logger.info(f"Received {signal_name}, flushing logs...")
    
    # Flush all handlers (especially OTLP which batches logs)
    flush_logging()
    
    logger.info("Shutdown complete")
    sys.exit(0)

# Register handlers for Gunicorn (SIGTERM) and Ctrl+C (SIGINT)
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# Create WSGI application
application = get_wsgi_application()

# === Django Settings Configuration (settings.py) ===
"""
# settings.py - CRITICAL CONFIGURATION

from faciliter_lib.config.logger_settings import LoggerSettings
from faciliter_lib.tracing.logger import setup_logging

# STEP 1: Disable Django's default logging (REQUIRED)
# See: https://docs.djangoproject.com/en/5.2/topics/logging/
LOGGING_CONFIG = None

# STEP 2: Configure faciliter-lib logging
LOGGER_SETTINGS = LoggerSettings.from_env()
setup_logging(
    app_name="my-django-app",
    logger_settings=LOGGER_SETTINGS,
    force=True
)

# Rest of your Django settings...
"""

# === Environment Variables (.env example) ===
"""
# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_ENABLED=true
LOG_FILE_PATH=logs/django.log
LOG_FILE_MAX_BYTES=10485760
LOG_FILE_BACKUP_COUNT=5

# OTLP (OpenTelemetry) Configuration
OTLP_ENABLED=true
OTLP_ENDPOINT=http://localhost:4318/v1/logs
OTLP_SERVICE_NAME=my-django-app
OTLP_SERVICE_VERSION=1.0.0
OTLP_LOG_LEVEL=INFO
OTLP_TIMEOUT=10
OTLP_INSECURE=false

# Optional: OVH Logs Data Platform
OVH_LDP_ENABLED=false
OVH_LDP_TOKEN=your-token-here
OVH_LDP_ENDPOINT=gra1.logs.ovh.com
"""

# === Example Django View ===
"""
# views.py
from faciliter_lib.tracing import LoggingContext
from faciliter_lib.tracing.logger import get_module_logger
from django.http import JsonResponse

logger = get_module_logger()

def api_view(request):
    # Add request context to all logs
    context = {
        'user_id': str(request.user.id) if request.user.is_authenticated else None,
        'session_id': request.session.session_key,
        'request_id': request.META.get('HTTP_X_REQUEST_ID'),
    }
    
    with LoggingContext(context):
        logger.info("API request received", extra={
            "method": request.method,
            "path": request.path,
        })
        
        try:
            # Process request
            result = {"message": "Success"}
            logger.info("Request completed successfully")
            return JsonResponse(result)
        except Exception as e:
            logger.error("Request failed", exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)
"""

# === Example Gunicorn Config ===
"""
# gunicorn.conf.py
workers = 4
worker_class = 'sync'
timeout = 30
graceful_timeout = 30

def worker_exit(server, worker):
    '''Flush logs when worker exits'''
    from faciliter_lib.tracing.logger import flush_logging
    flush_logging()

def on_exit(server):
    '''Flush logs when master exits'''
    from faciliter_lib.tracing.logger import flush_logging
    flush_logging()
"""

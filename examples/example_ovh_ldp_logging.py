"""Example: OVH Logs Data Platform Integration

This example demonstrates how to configure and use the logger with
OVH Logs Data Platform (LDP) via GELF protocol.

Environment Variables Required:
    OVH_LDP_ENABLED=true
    OVH_LDP_TOKEN=your-ldp-token
    OVH_LDP_ENDPOINT=gra1.logs.ovh.com  (or your region endpoint)
    OVH_LDP_PORT=12202  (optional, default: 12202)
    OVH_LDP_PROTOCOL=gelf_tcp  (optional, default: gelf_tcp)
    OVH_LDP_USE_TLS=true  (optional, default: true)
    
Optional Settings:
    LOG_LEVEL=INFO
    LOG_FILE_ENABLED=true
    LOG_FILE_PATH=logs/app.log
    OVH_LDP_ADDITIONAL_FIELDS='{"environment": "production", "service": "my-api"}'
"""

import os
import logging

# Configure environment (in practice, use .env file)
os.environ.update({
    "OVH_LDP_ENABLED": "true",
    "OVH_LDP_TOKEN": "your-ldp-token-here",
    "OVH_LDP_ENDPOINT": "gra1.logs.ovh.com",
    "OVH_LDP_PORT": "12202",
    "OVH_LDP_PROTOCOL": "gelf_tcp",
    "OVH_LDP_USE_TLS": "true",
    "LOG_LEVEL": "INFO",
    "LOG_FILE_ENABLED": "false",
    "OVH_LDP_ADDITIONAL_FIELDS": '{"environment": "demo", "service": "example"}',
})


def example_with_logger_settings():
    """Example 1: Using LoggerSettings directly"""
    from core_lib.config import LoggerSettings
    from core_lib.tracing.logger import setup_logging
    
    # Create logger settings from environment
    logger_settings = LoggerSettings.from_env()
    
    print("Logger Settings Configuration:")
    print(f"  Log Level: {logger_settings.log_level}")
    print(f"  File Logging: {logger_settings.file_logging}")
    print(f"  OVH LDP Enabled: {logger_settings.ovh_ldp_enabled}")
    print(f"  OVH LDP Endpoint: {logger_settings.ovh_ldp_endpoint}")
    print(f"  OVH LDP Protocol: {logger_settings.ovh_ldp_protocol}")
    print(f"  OVH LDP Additional Fields: {logger_settings.ovh_ldp_additional_fields}")
    print()
    
    # Setup logging with OVH LDP integration
    logger = setup_logging(
        app_name="example_app",
        logger_settings=logger_settings,
        force=True
    )
    
    # Test logging
    logger.info("Application started")
    logger.debug("Debug message - might not be sent based on level")
    logger.warning("Warning message with custom context", extra={"user_id": "12345"})
    logger.error("Error message example")
    
    try:
        1 / 0
    except Exception as e:
        logger.exception("Exception caught and logged with traceback")
    
    print("✓ Logs sent to OVH LDP via GELF TCP")


def example_with_standard_settings():
    """Example 2: Using StandardSettings with integrated LoggerSettings"""
    from core_lib.config import StandardSettings
    from core_lib.tracing.logger import setup_logging
    
    # Create standard settings (includes logger auto-detection)
    settings = StandardSettings.from_env()
    
    print("\nStandard Settings Configuration:")
    print(f"  App Name: {settings.app_name}")
    print(f"  Environment: {settings.environment}")
    print(f"  Logger Enabled: {settings.enable_logger}")
    
    if settings.logger:
        print(f"  OVH LDP Enabled: {settings.logger.ovh_ldp_enabled}")
        print(f"  OVH LDP Endpoint: {settings.logger.ovh_ldp_endpoint}")
    print()
    
    # Setup logging using settings
    if settings.enable_logger:
        logger = setup_logging(
            app_name=settings.app_name,
            logger_settings=settings.logger,
            force=True
        )
        
        logger.info("Using StandardSettings for unified configuration")
        logger.info("This simplifies managing all application settings together")
    else:
        print("Logger not enabled in StandardSettings")


def example_with_custom_fields():
    """Example 3: Custom fields and metadata in logs"""
    from core_lib.config import LoggerSettings
    from core_lib.tracing.logger import setup_logging
    
    # Create custom logger settings
    logger_settings = LoggerSettings(
        log_level="DEBUG",
        ovh_ldp_enabled=True,
        ovh_ldp_token=os.getenv("OVH_LDP_TOKEN"),
        ovh_ldp_endpoint=os.getenv("OVH_LDP_ENDPOINT"),
        ovh_ldp_port=12202,
        ovh_ldp_protocol="gelf_tcp",
        ovh_ldp_use_tls=True,
        ovh_ldp_additional_fields={
            "application": "my-microservice",
            "datacenter": "gra1",
            "version": "1.2.3",
            "team": "backend",
        }
    )
    
    logger = setup_logging(
        app_name="custom_app",
        logger_settings=logger_settings,
        force=True
    )
    
    print("\nCustom Fields Example:")
    logger.info("Request received", extra={
        "_request_id": "req-12345",
        "_user_id": "user-789",
        "_endpoint": "/api/users",
    })
    logger.info("All additional fields are sent to OVH LDP with GELF message")
    print("✓ Custom fields included in GELF messages")


def example_fallback_without_ovh():
    """Example 4: Logging without OVH LDP (console only)"""
    from core_lib.tracing.logger import setup_logging
    
    # Temporarily disable OVH LDP
    original_enabled = os.getenv("OVH_LDP_ENABLED")
    os.environ["OVH_LDP_ENABLED"] = "false"
    
    logger = setup_logging(app_name="fallback_app", force=True)
    
    print("\nFallback Mode (OVH LDP disabled):")
    logger.info("This goes to console only")
    logger.warning("File logging can still be enabled separately")
    print("✓ Standard console logging working")
    
    # Restore
    if original_enabled:
        os.environ["OVH_LDP_ENABLED"] = original_enabled


def example_validation():
    """Example 5: Settings validation"""
    from core_lib.config import LoggerSettings
    from core_lib.config.base_settings import SettingsError
    
    print("\nValidation Examples:")
    
    # Valid configuration
    try:
        valid_settings = LoggerSettings(
            ovh_ldp_enabled=True,
            ovh_ldp_token="token123",
            ovh_ldp_endpoint="gra1.logs.ovh.com",
            ovh_ldp_protocol="gelf_tcp",
        )
        print("✓ Valid settings passed validation")
    except SettingsError as e:
        print(f"✗ Validation failed: {e}")
    
    # Missing token
    try:
        invalid_settings = LoggerSettings(
            ovh_ldp_enabled=True,
            ovh_ldp_endpoint="gra1.logs.ovh.com",
        )
        print("✗ Should have failed - missing token")
    except SettingsError as e:
        print(f"✓ Caught expected error: {e}")
    
    # Invalid protocol
    try:
        invalid_settings = LoggerSettings(
            ovh_ldp_enabled=True,
            ovh_ldp_token="token123",
            ovh_ldp_endpoint="gra1.logs.ovh.com",
            ovh_ldp_protocol="invalid_protocol",
        )
        print("✗ Should have failed - invalid protocol")
    except SettingsError as e:
        print(f"✓ Caught expected error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("OVH Logs Data Platform (LDP) Integration Examples")
    print("=" * 60)
    
    print("\n⚠️  NOTE: These examples require valid OVH LDP credentials")
    print("Set OVH_LDP_TOKEN and OVH_LDP_ENDPOINT in your environment\n")
    
    # Run examples
    try:
        example_with_logger_settings()
    except Exception as e:
        print(f"Example 1 failed: {e}")
    
    try:
        example_with_standard_settings()
    except Exception as e:
        print(f"Example 2 failed: {e}")
    
    try:
        example_with_custom_fields()
    except Exception as e:
        print(f"Example 3 failed: {e}")
    
    try:
        example_fallback_without_ovh()
    except Exception as e:
        print(f"Example 4 failed: {e}")
    
    try:
        example_validation()
    except Exception as e:
        print(f"Example 5 failed: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed")
    print("=" * 60)

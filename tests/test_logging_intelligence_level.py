"""Integration test for logging context with intelligence_level."""

import logging
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from faciliter_lib.api_utils.fastapi_middleware import inject_from_logging_context
from faciliter_lib.tracing import (
    get_current_logging_context,
    LoggingContextFilter,
    install_logging_context_filter
)


@pytest.fixture
def app_with_logging():
    """Create a test FastAPI app with middleware and logging configured."""
    # Setup logging with context filter
    logger = logging.getLogger("test_app")
    logger.setLevel(logging.INFO)
    
    # Install context filter
    install_logging_context_filter(logger)
    
    app = FastAPI()
    
    @app.middleware("http")
    async def add_from_context(request: Request, call_next):
        return await inject_from_logging_context(request, call_next, tracing_client=None)
    
    @app.get("/test")
    async def test_endpoint():
        # Log something to verify the context is included
        logger.info("Test log message")
        context = get_current_logging_context()
        return {"context": context}
    
    return app, logger


def test_logging_includes_intelligence_level(app_with_logging, caplog):
    """Test that log records include intelligence_level attribute."""
    app, logger = app_with_logging
    client = TestClient(app)
    
    # Capture logs
    with caplog.at_level(logging.INFO, logger="test_app"):
        # Make a request with intelligence_level
        response = client.get("/test?intelligence_level=9")
        
        assert response.status_code == 200
        
        # Check that logs were captured
        assert len(caplog.records) > 0
        
        # Find the "Test log message" record
        log_record = None
        for record in caplog.records:
            if "Test log message" in record.message:
                log_record = record
                break
        
        assert log_record is not None, "Test log message not found in captured logs"
        
        # Verify the record has extra_attrs with intelligence_level
        assert hasattr(log_record, 'extra_attrs'), "Log record missing extra_attrs"
        assert 'intelligence.level' in log_record.extra_attrs
        assert log_record.extra_attrs['intelligence.level'] == 9


def test_logging_includes_from_fields_and_intelligence_level(app_with_logging, caplog):
    """Test that log records include both from fields and intelligence_level."""
    app, logger = app_with_logging
    client = TestClient(app)
    
    # Capture logs
    with caplog.at_level(logging.INFO, logger="test_app"):
        # Make a request with both from and intelligence_level
        from_param = '{"user_id":"user123","session_id":"sess456","company_id":"comp789"}'
        response = client.get(f'/test?from={from_param}&intelligence_level=7')
        
        assert response.status_code == 200
        
        # Find the "Test log message" record
        log_record = None
        for record in caplog.records:
            if "Test log message" in record.message:
                log_record = record
                break
        
        assert log_record is not None, "Test log message not found in captured logs"
        
        # Verify the record has all expected attributes
        assert hasattr(log_record, 'extra_attrs'), "Log record missing extra_attrs"
        assert log_record.extra_attrs['user.id'] == "user123"
        assert log_record.extra_attrs['session.id'] == "sess456"
        assert log_record.extra_attrs['organization.id'] == "comp789"
        assert log_record.extra_attrs['intelligence.level'] == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

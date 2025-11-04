"""Tests for FastAPI middleware utilities."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from faciliter_lib.api_utils.fastapi_middleware import inject_from_logging_context
from faciliter_lib.tracing import get_current_logging_context


@pytest.fixture
def app():
    """Create a test FastAPI app with middleware."""
    app = FastAPI()
    
    @app.middleware("http")
    async def add_from_context(request: Request, call_next):
        return await inject_from_logging_context(request, call_next, tracing_client=None)
    
    @app.get("/test")
    async def test_endpoint():
        # Get the current logging context to verify middleware worked
        context = get_current_logging_context()
        return {"context": context}
    
    return app


def test_middleware_extracts_intelligence_level(app):
    """Test that middleware extracts intelligence_level from query params."""
    client = TestClient(app)
    
    # Make a request with intelligence_level
    response = client.get("/test?intelligence_level=7")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify intelligence_level was added to context
    assert "context" in data
    assert "intelligence_level" in data["context"]
    assert data["context"]["intelligence_level"] == 7


def test_middleware_extracts_from_and_intelligence_level(app):
    """Test that middleware extracts both from and intelligence_level."""
    client = TestClient(app)
    
    # Make a request with both from and intelligence_level
    from_param = '{"user_id":"user123","session_id":"sess456"}'
    response = client.get(f'/test?from={from_param}&intelligence_level=8')
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify both from fields and intelligence_level were added to context
    assert "context" in data
    assert data["context"]["user_id"] == "user123"
    assert data["context"]["session_id"] == "sess456"
    assert data["context"]["intelligence_level"] == 8


def test_middleware_validates_intelligence_level_range(app):
    """Test that middleware validates intelligence_level is in range 0-10."""
    client = TestClient(app)
    
    # Test valid values
    response = client.get("/test?intelligence_level=0")
    assert response.json()["context"]["intelligence_level"] == 0
    
    response = client.get("/test?intelligence_level=10")
    assert response.json()["context"]["intelligence_level"] == 10
    
    # Test invalid values (should be ignored)
    response = client.get("/test?intelligence_level=-1")
    assert "intelligence_level" not in response.json()["context"]
    
    response = client.get("/test?intelligence_level=11")
    assert "intelligence_level" not in response.json()["context"]
    
    response = client.get("/test?intelligence_level=invalid")
    assert "intelligence_level" not in response.json()["context"]


def test_middleware_without_intelligence_level(app):
    """Test that middleware works when intelligence_level is not provided."""
    client = TestClient(app)
    
    response = client.get("/test")
    
    assert response.status_code == 200
    data = response.json()
    
    # Context should be empty or not contain intelligence_level
    assert "intelligence_level" not in data["context"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

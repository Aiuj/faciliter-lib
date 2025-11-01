"""Tests for service usage tracking functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from faciliter_lib.tracing.service_usage import (
    log_llm_usage,
    log_embedding_usage,
    log_ocr_usage,
    calculate_llm_cost,
    calculate_embedding_cost,
)


def test_calculate_llm_cost_known_model():
    """Test cost calculation for known models."""
    # GPT-4: $0.03 input, $0.06 output per 1K tokens
    cost = calculate_llm_cost("openai", "gpt-4", 1000, 500)
    expected = (1000 / 1000 * 0.03) + (500 / 1000 * 0.06)  # $0.03 + $0.03 = $0.06
    assert cost == pytest.approx(expected, rel=1e-6)


def test_calculate_llm_cost_unknown_model():
    """Test cost calculation for unknown models returns 0."""
    cost = calculate_llm_cost("custom", "unknown-model", 1000, 500)
    assert cost == 0.0


def test_calculate_embedding_cost_known_model():
    """Test cost calculation for known embedding models."""
    # text-embedding-3-small: $0.00002 per 1K tokens
    cost = calculate_embedding_cost("openai", "text-embedding-3-small", 5000)
    expected = 5000 / 1000 * 0.00002  # $0.0001
    assert cost == pytest.approx(expected, rel=1e-6)


def test_calculate_embedding_cost_unknown_model():
    """Test cost calculation for unknown models returns 0."""
    cost = calculate_embedding_cost("custom", "unknown-model", 5000)
    assert cost == 0.0


@patch('faciliter_lib.tracing.service_usage.logger')
def test_log_llm_usage_success(mock_logger):
    """Test logging LLM usage with valid data."""
    log_llm_usage(
        provider="openai",
        model="gpt-4o-mini",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        latency_ms=1500,
        structured=False,
        has_tools=True,
        search_grounding=False,
    )
    
    # Verify logger.info was called
    assert mock_logger.info.called
    call_args = mock_logger.info.call_args
    
    # Check message format
    message = call_args[0][0]
    assert "openai" in message
    assert "gpt-4o-mini" in message
    assert "150" in message  # Total tokens
    
    # Check extra_attrs
    extra = call_args[1]['extra']
    attrs = extra['extra_attrs']
    
    assert attrs['service.type'] == 'llm'
    assert attrs['service.provider'] == 'openai'
    assert attrs['service.model'] == 'gpt-4o-mini'
    assert attrs['tokens.input'] == 100
    assert attrs['tokens.output'] == 50
    assert attrs['tokens.total'] == 150
    assert attrs['latency_ms'] == 1500
    assert attrs['features.structured_output'] is False
    assert attrs['features.tools'] is True
    assert attrs['status'] == 'success'
    assert 'cost_usd' in attrs


@patch('faciliter_lib.tracing.service_usage.logger')
def test_log_llm_usage_with_error(mock_logger):
    """Test logging LLM usage with error."""
    log_llm_usage(
        provider="openai",
        model="gpt-4",
        error="Authentication failed",
    )
    
    assert mock_logger.info.called
    call_args = mock_logger.info.call_args
    extra = call_args[1]['extra']
    attrs = extra['extra_attrs']
    
    assert attrs['status'] == 'error'
    assert attrs['error'] == 'Authentication failed'


@patch('faciliter_lib.tracing.service_usage.logger')
def test_log_embedding_usage_success(mock_logger):
    """Test logging embedding usage with valid data."""
    log_embedding_usage(
        provider="openai",
        model="text-embedding-3-small",
        input_tokens=500,
        num_texts=10,
        embedding_dim=1536,
        latency_ms=250,
    )
    
    assert mock_logger.info.called
    call_args = mock_logger.info.call_args
    
    message = call_args[0][0]
    assert "openai" in message
    assert "text-embedding-3-small" in message
    assert "10" in message  # num_texts
    
    extra = call_args[1]['extra']
    attrs = extra['extra_attrs']
    
    assert attrs['service.type'] == 'embedding'
    assert attrs['service.provider'] == 'openai'
    assert attrs['service.model'] == 'text-embedding-3-small'
    assert attrs['tokens.input'] == 500
    assert attrs['embedding.num_texts'] == 10
    assert attrs['embedding.dimension'] == 1536
    assert attrs['latency_ms'] == 250
    assert attrs['status'] == 'success'
    assert 'cost_usd' in attrs


@patch('faciliter_lib.tracing.service_usage.logger')
def test_log_ocr_usage_success(mock_logger):
    """Test logging OCR usage with valid data."""
    log_ocr_usage(
        provider="azure-di",
        model="prebuilt-read",
        num_pages=5,
        latency_ms=3000,
        cost_override=0.05,
    )
    
    assert mock_logger.info.called
    call_args = mock_logger.info.call_args
    
    message = call_args[0][0]
    assert "azure-di" in message
    assert "5" in message  # num_pages
    
    extra = call_args[1]['extra']
    attrs = extra['extra_attrs']
    
    assert attrs['service.type'] == 'ocr'
    assert attrs['service.provider'] == 'azure-di'
    assert attrs['service.model'] == 'prebuilt-read'
    assert attrs['ocr.num_pages'] == 5
    assert attrs['latency_ms'] == 3000
    assert attrs['cost_usd'] == 0.05
    assert attrs['status'] == 'success'


@patch('faciliter_lib.tracing.service_usage.logger')
def test_log_llm_usage_with_metadata(mock_logger):
    """Test logging LLM usage with custom metadata."""
    log_llm_usage(
        provider="openai",
        model="gpt-4",
        input_tokens=100,
        output_tokens=50,
        metadata={"endpoint": "/api/chat", "version": "v2"},
    )
    
    call_args = mock_logger.info.call_args
    extra = call_args[1]['extra']
    attrs = extra['extra_attrs']
    
    # Custom metadata should be prefixed
    assert attrs['custom.endpoint'] == '/api/chat'
    assert attrs['custom.version'] == 'v2'


@patch('faciliter_lib.tracing.service_usage.logger')
def test_log_embedding_usage_with_error(mock_logger):
    """Test logging embedding usage with error."""
    log_embedding_usage(
        provider="infinity",
        model="BAAI/bge-small-en-v1.5",
        num_texts=5,
        error="Connection timeout",
    )
    
    call_args = mock_logger.info.call_args
    extra = call_args[1]['extra']
    attrs = extra['extra_attrs']
    
    assert attrs['status'] == 'error'
    assert attrs['error'] == 'Connection timeout'


def test_calculate_llm_cost_partial_match():
    """Test that partial model name matching works."""
    # Should match gpt-4o pricing for gpt-4o-2024-08-06
    cost = calculate_llm_cost("openai", "gpt-4o-2024-08-06", 1000, 500)
    expected = (1000 / 1000 * 0.005) + (500 / 1000 * 0.015)  # gpt-4o pricing
    assert cost == pytest.approx(expected, rel=1e-6)


def test_tokens_per_second_calculation():
    """Test that tokens_per_second is calculated correctly."""
    with patch('faciliter_lib.tracing.service_usage.logger') as mock_logger:
        log_llm_usage(
            provider="openai",
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            latency_ms=1500,  # 1.5 seconds
        )
        
        call_args = mock_logger.info.call_args
        extra = call_args[1]['extra']
        attrs = extra['extra_attrs']
        
        # 150 tokens / 1.5 seconds = 100 tokens/second
        assert attrs['tokens_per_second'] == pytest.approx(100.0, rel=1e-3)

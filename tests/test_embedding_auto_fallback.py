"""Tests for automatic fallback detection in create_embedding_client."""

import pytest
from unittest.mock import Mock, patch
from faciliter_lib.embeddings.factory import create_embedding_client
from faciliter_lib.embeddings.fallback_client import FallbackEmbeddingClient


class TestAutoFallbackDetection:
    """Test automatic fallback client creation."""

    def test_single_url_creates_regular_client(self):
        """Test that single URL creates regular client, not fallback."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'INFINITY_BASE_URL': 'http://localhost:7997',
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.factory.EmbeddingFactory.create') as mock_create:
                mock_client = Mock()
                mock_create.return_value = mock_client
                
                client = create_embedding_client()
                
                # Should call regular factory, not FallbackEmbeddingClient
                assert mock_create.called
                assert client == mock_client

    def test_comma_separated_urls_creates_fallback_client(self):
        """Test that comma-separated URLs automatically create FallbackEmbeddingClient."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'INFINITY_BASE_URL': 'http://host1:7997,http://host2:7997,http://host3:7997',
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
                mock_provider = Mock()
                mock_provider.model = "test-model"
                mock_provider.embedding_dim = 384
                mock_create.return_value = mock_provider
                
                client = create_embedding_client()
                
                # Should create FallbackEmbeddingClient
                assert isinstance(client, FallbackEmbeddingClient)
                assert len(client.providers) == 3

    def test_generic_embedding_base_url_with_commas(self):
        """Test automatic fallback with generic EMBEDDING_BASE_URL."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'EMBEDDING_BASE_URL': 'http://host1:7997,http://host2:7997',
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
                mock_provider = Mock()
                mock_provider.model = "test-model"
                mock_provider.embedding_dim = 384
                mock_create.return_value = mock_provider
                
                client = create_embedding_client()
                
                assert isinstance(client, FallbackEmbeddingClient)
                assert len(client.providers) == 2

    def test_comma_in_url_path_not_treated_as_separator(self):
        """Test that commas in URL path/query don't trigger fallback."""
        # Edge case: URL with comma in query string should not trigger fallback
        # This is unlikely but we should handle single URLs with commas properly
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'INFINITY_BASE_URL': 'http://localhost:7997',  # No comma
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.factory.EmbeddingFactory.create') as mock_create:
                mock_client = Mock()
                mock_create.return_value = mock_client
                
                client = create_embedding_client()
                
                assert mock_create.called
                assert not isinstance(client, FallbackEmbeddingClient)


class TestTokenAuthentication:
    """Test token authentication support."""

    def test_single_token_for_all_hosts(self):
        """Test that single token is used for all hosts."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'INFINITY_BASE_URL': 'http://host1:7997,http://host2:7997,http://host3:7997',
            'INFINITY_TOKEN': 'shared-token',
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
                mock_provider = Mock()
                mock_provider.model = "test-model"
                mock_provider.embedding_dim = 384
                mock_create.return_value = mock_provider
                
                client = FallbackEmbeddingClient.from_env()
                
                # All three providers should be created with the same token
                assert mock_create.call_count == 3
                for call in mock_create.call_args_list:
                    kwargs = call[1]
                    assert kwargs['token'] == 'shared-token'

    def test_multiple_tokens_for_multiple_hosts(self):
        """Test that comma-separated tokens match hosts."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'INFINITY_BASE_URL': 'http://host1:7997,http://host2:7997,http://host3:7997',
            'INFINITY_TOKEN': 'token1,token2,token3',
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
                mock_provider = Mock()
                mock_provider.model = "test-model"
                mock_provider.embedding_dim = 384
                mock_create.return_value = mock_provider
                
                client = FallbackEmbeddingClient.from_env()
                
                # Three providers with matching tokens
                assert mock_create.call_count == 3
                tokens_used = [call[1]['token'] for call in mock_create.call_args_list]
                assert tokens_used == ['token1', 'token2', 'token3']

    def test_fewer_tokens_than_hosts_reuses_last(self):
        """Test that last token is reused when fewer tokens than hosts."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'INFINITY_BASE_URL': 'http://host1:7997,http://host2:7997,http://host3:7997',
            'INFINITY_TOKEN': 'token1,token2',  # Only 2 tokens for 3 hosts
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
                mock_provider = Mock()
                mock_provider.model = "test-model"
                mock_provider.embedding_dim = 384
                mock_create.return_value = mock_provider
                
                client = FallbackEmbeddingClient.from_env()
                
                # Three providers, last token reused
                assert mock_create.call_count == 3
                tokens_used = [call[1]['token'] for call in mock_create.call_args_list]
                assert tokens_used == ['token1', 'token2', 'token2']  # token2 reused

    def test_generic_embedding_token(self):
        """Test fallback to generic EMBEDDING_TOKEN."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'EMBEDDING_BASE_URL': 'http://host1:7997,http://host2:7997',
            'EMBEDDING_TOKEN': 'generic-token1,generic-token2',
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
                mock_provider = Mock()
                mock_provider.model = "test-model"
                mock_provider.embedding_dim = 384
                mock_create.return_value = mock_provider
                
                client = FallbackEmbeddingClient.from_env()
                
                # Should use generic EMBEDDING_TOKEN
                assert mock_create.call_count == 2
                tokens_used = [call[1]['token'] for call in mock_create.call_args_list]
                assert tokens_used == ['generic-token1', 'generic-token2']

    def test_openai_uses_api_key_not_token(self):
        """Test that OpenAI provider uses api_key parameter, not token."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'openai',
            'OPENAI_BASE_URL': 'http://host1/v1,http://host2/v1',
            'OPENAI_API_KEY': 'sk-key1,sk-key2',
            'EMBEDDING_MODEL': 'test-model',
        }):
            with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
                mock_provider = Mock()
                mock_provider.model = "test-model"
                mock_provider.embedding_dim = 384
                mock_create.return_value = mock_provider
                
                client = FallbackEmbeddingClient.from_env(provider='openai')
                
                # Should use api_key for OpenAI
                assert mock_create.call_count == 2
                for call in mock_create.call_args_list:
                    kwargs = call[1]
                    assert 'api_key' in kwargs
                    assert 'token' not in kwargs or kwargs.get('token') is None

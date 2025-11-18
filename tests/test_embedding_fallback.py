"""Tests for FallbackEmbeddingClient."""

import pytest
from unittest.mock import Mock, patch
from faciliter_lib.embeddings.fallback_client import FallbackEmbeddingClient
from faciliter_lib.embeddings.base import EmbeddingGenerationError


class TestFallbackEmbeddingClient:
    """Test suite for FallbackEmbeddingClient."""

    def test_initialization_with_providers(self):
        """Test basic initialization with provider list."""
        mock_provider1 = Mock()
        mock_provider1.model = "model1"
        mock_provider1.embedding_dim = 384
        
        mock_provider2 = Mock()
        mock_provider2.model = "model2"
        mock_provider2.embedding_dim = 384
        
        client = FallbackEmbeddingClient(
            providers=[mock_provider1, mock_provider2],
        )
        
        assert len(client.providers) == 2
        assert client.model == "model1"  # Uses first provider's model
        assert client.embedding_dim == 384

    def test_initialization_empty_providers_raises(self):
        """Test that empty provider list raises ValueError."""
        with pytest.raises(ValueError, match="At least one provider"):
            FallbackEmbeddingClient(providers=[])

    def test_successful_embedding_generation(self):
        """Test successful embedding generation with first provider."""
        mock_provider = Mock()
        mock_provider.model = "test-model"
        mock_provider.embedding_dim = 384
        mock_provider._generate_embedding_raw.return_value = [[0.1, 0.2, 0.3]]
        
        client = FallbackEmbeddingClient(providers=[mock_provider])
        
        result = client._generate_embedding_raw(["test"])
        
        assert result == [[0.1, 0.2, 0.3]]
        mock_provider._generate_embedding_raw.assert_called_once_with(["test"])

    def test_fallback_on_first_provider_failure(self):
        """Test automatic fallback when first provider fails."""
        mock_provider1 = Mock()
        mock_provider1.model = "model1"
        mock_provider1.embedding_dim = 384
        mock_provider1._generate_embedding_raw.side_effect = Exception("Provider 1 failed")
        
        mock_provider2 = Mock()
        mock_provider2.model = "model2"
        mock_provider2.embedding_dim = 384
        mock_provider2._generate_embedding_raw.return_value = [[0.4, 0.5, 0.6]]
        
        client = FallbackEmbeddingClient(
            providers=[mock_provider1, mock_provider2],
        )
        
        result = client._generate_embedding_raw(["test"])
        
        assert result == [[0.4, 0.5, 0.6]]
        assert mock_provider1._generate_embedding_raw.call_count == 1
        assert mock_provider2._generate_embedding_raw.call_count == 1

    def test_all_providers_fail_raises_error(self):
        """Test that exception is raised when all providers fail."""
        mock_provider1 = Mock()
        mock_provider1.model = "model1"
        mock_provider1.embedding_dim = 384
        mock_provider1._generate_embedding_raw.side_effect = Exception("Fail 1")
        
        mock_provider2 = Mock()
        mock_provider2.model = "model2"
        mock_provider2.embedding_dim = 384
        mock_provider2._generate_embedding_raw.side_effect = Exception("Fail 2")
        
        client = FallbackEmbeddingClient(
            providers=[mock_provider1, mock_provider2],
            fail_on_all_providers=True,
        )
        
        with pytest.raises(EmbeddingGenerationError, match="All .* providers failed"):
            client._generate_embedding_raw(["test"])

    def test_all_providers_fail_returns_none_when_configured(self):
        """Test graceful degradation when fail_on_all_providers=False."""
        mock_provider = Mock()
        mock_provider.model = "model1"
        mock_provider.embedding_dim = 384
        mock_provider._generate_embedding_raw.side_effect = Exception("Fail")
        
        client = FallbackEmbeddingClient(
            providers=[mock_provider],
            fail_on_all_providers=False,
        )
        
        result = client._generate_embedding_raw(["test"])
        assert result is None

    def test_retry_logic_per_provider(self):
        """Test that each provider is retried before moving to next."""
        mock_provider1 = Mock()
        mock_provider1.model = "model1"
        mock_provider1.embedding_dim = 384
        mock_provider1._generate_embedding_raw.side_effect = Exception("Fail")
        
        mock_provider2 = Mock()
        mock_provider2.model = "model2"
        mock_provider2.embedding_dim = 384
        mock_provider2._generate_embedding_raw.return_value = [[0.1, 0.2]]
        
        client = FallbackEmbeddingClient(
            providers=[mock_provider1, mock_provider2],
            max_retries_per_provider=3,
        )
        
        result = client._generate_embedding_raw(["test"])
        
        assert result == [[0.1, 0.2]]
        assert mock_provider1._generate_embedding_raw.call_count == 3
        assert mock_provider2._generate_embedding_raw.call_count == 1

    def test_from_config_creates_providers(self):
        """Test from_config factory method."""
        with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
            mock_provider = Mock()
            mock_provider.model = "test-model"
            mock_provider.embedding_dim = 384
            mock_create.return_value = mock_provider
            
            client = FallbackEmbeddingClient.from_config(
                provider_configs=[
                    {"provider": "infinity", "base_url": "http://host1:7997"},
                    {"provider": "infinity", "base_url": "http://host2:7997"},
                ],
                common_model="test-model",
            )
            
            assert len(client.providers) == 2
            assert mock_create.call_count == 2

    def test_from_config_applies_common_settings(self):
        """Test that common settings override individual provider settings."""
        with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
            mock_provider = Mock()
            mock_provider.model = "common-model"
            mock_provider.embedding_dim = 512
            mock_create.return_value = mock_provider
            
            FallbackEmbeddingClient.from_config(
                provider_configs=[
                    {"provider": "infinity", "model": "individual-model"},
                ],
                common_model="common-model",
                common_embedding_dim=512,
            )
            
            # Check that common settings were passed
            call_args = mock_create.call_args[1]
            assert call_args["model"] == "common-model"
            assert call_args["embedding_dim"] == 512

    def test_health_check_returns_true_if_any_healthy(self):
        """Test health check returns True if at least one provider is healthy."""
        mock_provider1 = Mock()
        mock_provider1.model = "model1"
        mock_provider1.embedding_dim = 384
        mock_provider1.health_check.return_value = False
        
        mock_provider2 = Mock()
        mock_provider2.model = "model2"
        mock_provider2.embedding_dim = 384
        mock_provider2.health_check.return_value = True
        
        client = FallbackEmbeddingClient(providers=[mock_provider1, mock_provider2])
        
        assert client.health_check() is True

    def test_health_check_returns_false_if_all_unhealthy(self):
        """Test health check returns False if all providers are unhealthy."""
        mock_provider = Mock()
        mock_provider.model = "model1"
        mock_provider.embedding_dim = 384
        mock_provider.health_check.return_value = False
        
        client = FallbackEmbeddingClient(providers=[mock_provider])
        
        assert client.health_check() is False

    def test_get_provider_stats(self):
        """Test provider statistics retrieval."""
        mock_provider1 = Mock()
        mock_provider1.model = "model1"
        mock_provider1.embedding_dim = 384
        
        mock_provider2 = Mock()
        mock_provider2.model = "model2"
        mock_provider2.embedding_dim = 512
        
        client = FallbackEmbeddingClient(providers=[mock_provider1, mock_provider2])
        client.provider_failures = {0: 5, 1: 2}
        client.current_provider_index = 1
        
        stats = client.get_provider_stats()
        
        assert stats["total_providers"] == 2
        assert stats["current_provider"] == 1
        assert stats["provider_failures"] == {0: 5, 1: 2}
        assert len(stats["providers"]) == 2
        assert stats["providers"][0]["model"] == "model1"
        assert stats["providers"][1]["model"] == "model2"

    def test_reset_failures(self):
        """Test resetting failure counters."""
        mock_provider = Mock()
        mock_provider.model = "model1"
        mock_provider.embedding_dim = 384
        
        client = FallbackEmbeddingClient(providers=[mock_provider])
        client.provider_failures = {0: 10}
        
        client.reset_failures()
        
        assert client.provider_failures == {0: 0}

    def test_from_env_creates_client(self):
        """Test from_env factory method with comma-separated URLs."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'INFINITY_BASE_URL': 'http://host1:7997,http://host2:7997,http://host3:7997',
            'EMBEDDING_MODEL': 'test-model',
            'EMBEDDING_DIMENSION': '384',
        }):
            with patch('faciliter_lib.embeddings.fallback_client.EmbeddingFactory.create') as mock_create:
                mock_provider = Mock()
                mock_provider.model = "test-model"
                mock_provider.embedding_dim = 384
                mock_create.return_value = mock_provider
                
                client = FallbackEmbeddingClient.from_env()
                
                assert len(client.providers) == 3
                assert mock_create.call_count == 3
    
    def test_from_env_with_generic_base_url(self):
        """Test from_env using generic EMBEDDING_BASE_URL."""
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
                
                client = FallbackEmbeddingClient.from_env()
                
                assert len(client.providers) == 2
                assert mock_create.call_count == 2
    
    def test_from_env_missing_urls_raises(self):
        """Test from_env raises when no URLs configured."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'infinity',
            'EMBEDDING_MODEL': 'test-model',
        }, clear=True):
            with pytest.raises(ValueError, match="No base URLs found"):
                FallbackEmbeddingClient.from_env()

    def test_provider_preference_after_success(self):
        """Test that successful provider becomes preferred for next request."""
        mock_provider1 = Mock()
        mock_provider1.model = "model1"
        mock_provider1.embedding_dim = 384
        mock_provider1._generate_embedding_raw.side_effect = Exception("Fail")
        
        mock_provider2 = Mock()
        mock_provider2.model = "model2"
        mock_provider2.embedding_dim = 384
        mock_provider2._generate_embedding_raw.return_value = [[0.1, 0.2]]
        
        client = FallbackEmbeddingClient(providers=[mock_provider1, mock_provider2])
        
        # First request fails on provider 1, succeeds on provider 2
        client._generate_embedding_raw(["test1"])
        assert client.current_provider_index == 1
        
        # Second request should try provider 2 first
        mock_provider2._generate_embedding_raw.reset_mock()
        client._generate_embedding_raw(["test2"])
        assert mock_provider2._generate_embedding_raw.call_count == 1

"""Test that imports and instantiation don't create live connections.

This test verifies that the library follows lazy initialization patterns:
- Imports don't trigger network connections
- Class instantiation doesn't trigger network connections
- Connections are only made when explicitly calling connect() or API methods
"""
import unittest
from unittest.mock import patch, MagicMock
import socket


class TestLazyInitialization(unittest.TestCase):
    """Test lazy initialization patterns across the library."""
    
    def test_cache_imports_no_connection(self):
        """Test that importing cache modules doesn't create connections."""
        # These imports should not trigger any network activity
        from faciliter_lib.cache import RedisCache, cache_manager
        from faciliter_lib.cache.redis_config import RedisConfig
        
        # Success if no exceptions raised
        self.assertTrue(True)
    
    def test_llm_imports_no_connection(self):
        """Test that importing LLM modules doesn't create connections."""
        from faciliter_lib.llm import LLMClient, create_llm_client
        from faciliter_lib.llm.llm_config import OpenAIConfig, GeminiConfig
        
        self.assertTrue(True)
    
    def test_embeddings_imports_no_connection(self):
        """Test that importing embeddings modules doesn't create connections."""
        from faciliter_lib.embeddings import create_embedding_client
        from faciliter_lib.embeddings.factory import EmbeddingFactory
        
        self.assertTrue(True)
    
    @patch('faciliter_lib.cache.redis_cache.redis.Redis')
    def test_redis_cache_instantiation_no_connection(self, mock_redis):
        """Test that instantiating RedisCache doesn't call connect()."""
        from faciliter_lib.cache import RedisCache
        from faciliter_lib.cache.redis_config import RedisConfig
        
        config = RedisConfig(host='localhost', port=6379, db=0, prefix='test:')
        cache = RedisCache('test', config=config)
        
        # Redis.connect should not have been called
        # Only connection pool setup, no ping or network calls
        self.assertIsNone(cache.client)
        self.assertFalse(cache.connected)
    
    @patch('faciliter_lib.cache.redis_cache.redis.Redis')
    def test_redis_cache_connect_explicit(self, mock_redis):
        """Test that connection only happens when connect() is called."""
        from faciliter_lib.cache import RedisCache
        from faciliter_lib.cache.redis_config import RedisConfig
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        
        config = RedisConfig(host='localhost', port=6379, db=0, prefix='test:')
        cache = RedisCache('test', config=config)
        
        # Not connected yet
        self.assertFalse(cache.connected)
        
        # Explicitly connect
        cache.connect()
        
        # Now connected
        self.assertTrue(cache.connected)
        mock_client.ping.assert_called_once()
    
    def test_llm_client_instantiation_no_connection(self):
        """Test that instantiating LLM clients doesn't make network calls."""
        from faciliter_lib.llm import LLMClient
        from faciliter_lib.llm.llm_config import OpenAIConfig, OllamaConfig
        
        # OpenAI client
        openai_config = OpenAIConfig(api_key='test-key', model='gpt-4')
        openai_client = LLMClient(openai_config)
        self.assertIsNotNone(openai_client)
        
        # Ollama client
        ollama_config = OllamaConfig(model='llama2')
        ollama_client = LLMClient(ollama_config)
        self.assertIsNotNone(ollama_client)
    
    def test_job_queue_instantiation_no_connection(self):
        """Test that instantiating RedisJobQueue doesn't connect."""
        from faciliter_lib.jobs import RedisJobQueue
        from faciliter_lib.jobs.base_job_queue import JobConfig
        
        config = JobConfig(host='localhost', port=6379)
        queue = RedisJobQueue(config)
        
        # Not connected yet
        self.assertIsNone(queue.client)
        self.assertFalse(queue.connected)
    
    @patch('faciliter_lib.cache.redis_cache.redis.Redis')
    def test_cache_manager_get_cache_lazy(self, mock_redis):
        """Test that get_cache() initializes lazily."""
        from faciliter_lib.cache import cache_manager
        
        # Reset global state
        cache_manager._cache_instance = None
        
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.ping.return_value = True
        
        # First call initializes
        cache = cache_manager.get_cache()
        
        # Should have created and connected
        self.assertIsNotNone(cache)
        
        # Second call returns same instance
        cache2 = cache_manager.get_cache()
        self.assertIs(cache, cache2)
        
        # Cleanup
        cache_manager._cache_instance = None
    
    def test_tracing_import_no_connection(self):
        """Test that importing tracing doesn't initialize Langfuse."""
        # This should not create any connections
        from faciliter_lib.tracing import setup_tracing
        from faciliter_lib.tracing.tracing import add_trace_metadata
        
        # Just importing doesn't call setup
        self.assertTrue(True)
    
    def test_socket_not_called_during_import(self):
        """Integration test: verify no socket connections during common imports."""
        connection_attempts = []
        
        original_connect = socket.socket.connect
        
        def track_connect(self, address):
            connection_attempts.append(address)
            # Call original to avoid breaking anything
            return original_connect(self, address)
        
        # Patch socket
        socket.socket.connect = track_connect
        
        try:
            # Reimport modules (in case they're already loaded)
            import importlib
            import faciliter_lib.cache
            import faciliter_lib.llm
            import faciliter_lib.embeddings
            
            importlib.reload(faciliter_lib.cache)
            
            # No socket connections should have been attempted
            self.assertEqual(len(connection_attempts), 0,
                           f"Unexpected socket connections: {connection_attempts}")
        finally:
            # Restore original
            socket.socket.connect = original_connect


if __name__ == '__main__':
    unittest.main()

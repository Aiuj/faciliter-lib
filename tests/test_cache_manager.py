import pytest
from faciliter_lib.cache.cache_manager import (
    set_cache,
    get_cache,
    cache_get,
    cache_set,
    RedisCache,
)

def test_cache_set_and_get(monkeypatch):
    # Reset the global cache instance to ensure test isolation
    import faciliter_lib.cache.cache_manager as cache_module
    cache_module._cache_instance = None
    
    # Use a dummy RedisCache for isolation if needed, or rely on local Redis
    set_cache(ttl=10)
    input_data = {"foo": "bar"}
    output_data = {"result": 123}
    cache_set(input_data, output_data)
    assert cache_get(input_data) == output_data

def test_cache_ttl(monkeypatch):
    # Reset the global cache instance to ensure test isolation
    import faciliter_lib.cache.cache_manager as cache_module
    cache_module._cache_instance = None
    
    # Use a mock Redis client to simulate TTL expiration
    class MockRedis:
        def __init__(self):
            self.store = {}
            self.expiry = {}
            self.expired_keys = set()
        def setex(self, key, ttl, value):
            self.store[key] = value
            self.expiry[key] = ttl
            # Remove from expired keys when setting a new value
            self.expired_keys.discard(key)
        def get(self, key):
            # Check if key is manually marked as expired
            if key in self.expired_keys:
                return None
            return self.store.get(key)
        def expire(self, key, ttl):
            self.expiry[key] = ttl
        def ping(self):
            return True

    mock_redis = MockRedis()
    def mock_connect(self):
        self.client = mock_redis
        self.connected = True

    monkeypatch.setattr('faciliter_lib.cache.cache_manager.RedisCache.connect', mock_connect)
    set_cache(ttl=10)  # Use a longer TTL initially
    input_data = {"ttl": "test"}
    output_data = {"value": 42}
    cache_set(input_data, output_data)
    assert cache_get(input_data) == output_data
    # Simulate time passing by marking the key as expired
    key = get_cache()._make_key(input_data)
    mock_redis.expired_keys.add(key)
    assert cache_get(input_data) is None

def test_direct_cache_instance(monkeypatch):
    cache = RedisCache("pytest_direct")
    cache.connect()
    if not cache.connected:
        pytest.skip("Redis not available for direct instance test")
    input_data = {"direct": "yes"}
    output_data = {"ok": True}
    cache.set(input_data, output_data, ttl=5)
    assert cache.get(input_data) == output_data

def test_set_cache_singleton(monkeypatch):
    # Reset the global cache instance to ensure test isolation
    import faciliter_lib.cache.cache_manager as cache_module
    cache_module._cache_instance = None
    
    set_cache(ttl=5)
    cache1 = get_cache()
    set_cache(ttl=10)
    cache2 = get_cache()
    assert cache1 is cache2

def test_cache_get_returns_none_for_missing(monkeypatch):
    # Reset the global cache instance to ensure test isolation
    import faciliter_lib.cache.cache_manager as cache_module
    cache_module._cache_instance = None
    
    set_cache(ttl=5)
    input_data = {"missing": "entry"}
    assert cache_get(input_data) is None

# ...add more tests as needed...

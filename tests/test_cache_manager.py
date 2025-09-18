import pytest
from faciliter_lib.cache.cache_manager import (
    set_cache,
    get_cache,
    cache_get,
    cache_set,
    RedisCache,
)

class MockRedis:
    def __init__(self):
        self.store = {}
        self.expiry = {}
        self.expired_keys = set()
    
    def setex(self, key, ttl, value):
        self.store[key] = value
        self.expiry[key] = ttl
        self.expired_keys.discard(key)
    
    def get(self, key):
        if key in self.expired_keys:
            return None
        return self.store.get(key)
    
    def expire(self, key, ttl):
        self.expiry[key] = ttl
    
    def ping(self):
        return True
    
    def set(self, key, value):
        self.store[key] = value
    
    def delete(self, key):
        self.store.pop(key, None)
        self.expiry.pop(key, None)
        self.expired_keys.discard(key)

@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Auto-use fixture that mocks Redis for all tests in this module"""
    mock_redis_instance = MockRedis()
    
    def mock_redis_connection(*args, **kwargs):
        return mock_redis_instance
    
    # Mock the redis.Redis class
    monkeypatch.setattr('redis.Redis', mock_redis_connection)
    monkeypatch.setattr('faciliter_lib.cache.redis_cache.redis.Redis', mock_redis_connection)
    # Also mock the valkey client so ValkeyCache uses the same mocked backend
    # This makes Valkey a drop-in for Redis in tests.
    try:
        monkeypatch.setattr('valkey.Valkey', mock_redis_connection)
    except Exception:
        # If valkey isn't installed in the test environment, that's fine —
        # the cache manager will fall back to Redis.
        pass
    try:
        monkeypatch.setattr('faciliter_lib.cache.valkey_cache.valkey.Valkey', mock_redis_connection)
    except Exception:
        pass
    
    # Reset the global cache instance for test isolation
    import faciliter_lib.cache.cache_manager as cache_module
    cache_module._cache_instance = None
    
    yield mock_redis_instance

def test_cache_set_and_get():
    set_cache(ttl=10)
    input_data = {"foo": "bar"}
    output_data = {"result": 123}
    cache_set(input_data, output_data)
    assert cache_get(input_data) == output_data

def test_cache_ttl(mock_redis):
    set_cache(ttl=10)
    input_data = {"ttl": "test"}
    output_data = {"value": 42}
    cache_set(input_data, output_data)
    assert cache_get(input_data) == output_data
    
    # Simulate TTL expiration
    key = get_cache()._make_key(input_data)
    mock_redis.expired_keys.add(key)
    assert cache_get(input_data) is None

def test_direct_cache_instance():
    cache = RedisCache("pytest_direct")
    cache.connect()
    # With mocked Redis, connection should always succeed
    assert cache.connected
    input_data = {"direct": "yes"}
    output_data = {"ok": True}
    cache.set(input_data, output_data, ttl=5)
    assert cache.get(input_data) == output_data

def test_set_cache_singleton():
    set_cache(ttl=5)
    cache1 = get_cache()
    set_cache(ttl=10)
    cache2 = get_cache()
    assert cache1 is cache2

def test_cache_get_returns_none_for_missing():
    set_cache(ttl=5)
    input_data = {"missing": "entry"}
    assert cache_get(input_data) is None

# ...existing code...

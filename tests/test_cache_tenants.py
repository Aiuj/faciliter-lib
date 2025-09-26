import pytest
from faciliter_lib.cache.cache_manager import (
    set_cache,
    cache_set,
    cache_get,
    cache_clear_company,
    cache_clear_global,
    cache_clear_all,
    get_cache,
)

class MockRedis:
    def __init__(self):
        self.store = {}
        self.expiry = {}
        self.expired_keys = set()
        self.sets = {}

    # Key-value operations
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

    def delete(self, *keys):
        for key in keys:
            self.store.pop(key, None)
            self.expiry.pop(key, None)
            self.expired_keys.discard(key)
            self.sets.pop(key, None)

    # Set operations for registry
    def sadd(self, key, *members):
        self.sets.setdefault(key, set()).update(members)

    def smembers(self, key):
        return self.sets.get(key, set())

    # Scan implementation to iterate registry keys
    def scan(self, cursor=0, match=None, count=10):
        keys = list(self.sets.keys())
        if match:
            import fnmatch
            keys = [k for k in keys if fnmatch.fnmatch(k, match.replace('*', '*'))]
        return 0, keys  # Single batch

    def ping(self):
        return True

@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    mock_instance = MockRedis()
    def mock_conn(*args, **kwargs):
        return mock_instance
    monkeypatch.setattr('redis.Redis', mock_conn)
    monkeypatch.setattr('faciliter_lib.cache.redis_cache.redis.Redis', mock_conn)
    try:
        monkeypatch.setattr('valkey.Valkey', mock_conn)
    except Exception:
        pass
    try:
        monkeypatch.setattr('faciliter_lib.cache.valkey_cache.valkey.Valkey', mock_conn)
    except Exception:
        pass
    import faciliter_lib.cache.cache_manager as cm
    cm._cache_instance = None
    yield mock_instance


def test_tenant_isolation_and_clear_company():
    set_cache(ttl=60)
    cache_set({'k':1}, 'global-value')
    cache_set({'k':1}, 'tenant-a-value', company_id='A')
    cache_set({'k':1}, 'tenant-b-value', company_id='B')

    assert cache_get({'k':1}) == 'global-value'
    assert cache_get({'k':1}, company_id='A') == 'tenant-a-value'
    assert cache_get({'k':1}, company_id='B') == 'tenant-b-value'

    # Clear tenant A only
    cache_clear_company('A')
    assert cache_get({'k':1}, company_id='A') is None
    assert cache_get({'k':1}, company_id='B') == 'tenant-b-value'
    # Global unaffected
    assert cache_get({'k':1}) == 'global-value'


def test_clear_global_only():
    set_cache(ttl=60)
    cache_set({'k':2}, 'global', company_id=None)
    cache_set({'k':2}, 'tenant-x', company_id='X')
    cache_clear_global()
    assert cache_get({'k':2}) is None
    assert cache_get({'k':2}, company_id='X') == 'tenant-x'


def test_clear_all():
    set_cache(ttl=60)
    cache_set({'k':3}, 'g')
    cache_set({'k':3}, 'ta', company_id='A')
    cache_set({'k':3}, 'tb', company_id='B')
    cache_clear_all()
    assert cache_get({'k':3}) is None
    assert cache_get({'k':3}, company_id='A') is None
    assert cache_get({'k':3}, company_id='B') is None


def test_key_structure_contains_tenant():
    set_cache(ttl=60)
    cache = get_cache()
    key_global = cache._make_key({'x':1})
    key_tenant = cache._make_key({'x':1}, company_id='COMP')
    assert 'tenant:COMP' in key_tenant
    assert 'tenant:COMP' not in key_global
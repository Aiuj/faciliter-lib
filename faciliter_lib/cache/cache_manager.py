# cache_manager.py
# Cache manager with support for Redis and Valkey providers
import os
from typing import Any, Optional, Literal, Union, TYPE_CHECKING
import logging
from .base_cache import BaseCache
from .redis_cache import RedisCache
from .redis_config import RedisConfig

if TYPE_CHECKING:
    from .valkey_config import ValkeyConfig

try:
    from .valkey_cache import ValkeyCache
    from .valkey_config import ValkeyConfig
    VALKEY_AVAILABLE = True
except ImportError:
    VALKEY_AVAILABLE = False
    ValkeyCache = None
    ValkeyConfig = None

CacheProvider = Literal["redis", "valkey", "auto"]

# Module docstring: brief overview of responsibilities
"""Cache manager helpers to create and manage a global cache instance.

This module centralizes cache backend selection (redis | valkey | auto),
creation and a simple global accessor API used by the rest of the library.
It performs runtime detection of available client libraries and provides
helpers to convert configs when necessary.
"""


def _env_provider_preference() -> CacheProvider:
    """Return the cache backend preference read from the environment.

    Reads CACHE_BACKEND and normalizes to one of: "redis", "valkey", "auto".
    Defaults to "auto" when the environment variable is not present or invalid.
    """
    env = os.getenv("CACHE_BACKEND", "auto").lower()
    if env in ("redis", "valkey", "auto"):
        return env  # type: ignore[return-value]
    return "auto"


def create_cache(
    provider: CacheProvider = "auto",
    name: str = "",
    config: Optional[Any] = None,
    ttl: Optional[int] = None,
    time_out: Optional[int] = None,
) -> BaseCache:
    """Instantiate a cache implementation based on the requested provider.

    Parameters:
        provider: "redis", "valkey" or "auto". If "auto", this function will
            consult environment preference and the auto-detection helper.
        name: Optional name/namespace for the cache instance.
        config: Optional provider-specific config object (RedisConfig or ValkeyConfig).
        ttl: Optional time-to-live to override default config.
        time_out: Optional connection timeout override.

    Returns:
        An instance of BaseCache for the selected provider.

    Notes:
        - If the caller supplies a RedisConfig but requests the valkey provider,
          the RedisConfig will be converted into a ValkeyConfig (when Valkey
          types are available) as Valkey is treated as a Redis-compatible drop-in.
    """
    if provider == "auto":
        provider = _env_provider_preference()
        # If still auto, fall back to auto-detection based on available envs
        if provider == "auto":
            provider = _auto_detect_provider()

    # If caller passed a RedisConfig but requested valkey, convert it
    if provider == "valkey" and isinstance(config, RedisConfig) and not isinstance(config, ValkeyConfig):
        # Cast by creating a ValkeyConfig from the RedisConfig values
        # This preserves common fields and applies TTL/timeout fallbacks.
        cfg = ValkeyConfig(
            host=config.host,
            port=config.port,
            db=config.db,
            prefix=getattr(config, "prefix", "cache:"),
            ttl=getattr(config, "ttl", None) or ttl,
            password=getattr(config, "password", None),
            time_out=getattr(config, "time_out", None) or time_out,
        )
        config = cfg

    if provider == "redis":
        redis_config = config if isinstance(config, RedisConfig) else None
        return RedisCache(name=name, config=redis_config, ttl=ttl, time_out=time_out)
    elif provider == "valkey":
        valkey_config = config if isinstance(config, ValkeyConfig) else None
        return ValkeyCache(name=name, config=valkey_config, ttl=ttl, time_out=time_out)
    else:
        raise ValueError(f"Unsupported cache provider: {provider}")


def _auto_detect_provider() -> CacheProvider:
    """Auto-detect the preferred cache provider based on installed libraries.

    Preference order:
      1. valkey if its client library is importable
      2. redis if valkey is not available but redis client is installed
      3. 'redis' as a conventional fallback when no client libs are installed

    Returns:
        "valkey" | "redis" | "redis" (conventional fallback)
    """
    # Prefer valkey if its client library is available
    try:
        import valkey as _valkey  # type: ignore

        # If VALKEY envs are present or the client lib exists, prefer valkey
        return "valkey"
    except Exception:
        # valkey library not installed, try redis
        try:
            import redis as _redis  # type: ignore
            return "redis"
        except Exception:
            # No cache client libraries installed — return 'redis' as conventional
            # value; callers (e.g., set_cache) will handle the absence of client libs.
            return "redis"


_cache_instance = None


def set_cache(
    provider: CacheProvider = "auto",
    config: Optional[Any] = None,
    ttl: Optional[int] = None,
    time_out: Optional[int] = None,
):
    """Initialize the global cache instance.

    This function will:
      - Respect an explicit provider argument or the CACHE_BACKEND env var.
      - Fall back between valkey and redis depending on installed clients.
      - Create and connect the selected cache instance and set the global.

    Returns:
        True when a usable cache instance was created and connected.
        False when caching is disabled or instantiation/connection failed.

    Side effects:
        Sets the module-level _cache_instance to the instance or False.
    """
    global _cache_instance
    if _cache_instance is not None and _cache_instance is not False:
        return True
    try:
        # If provider is auto, allow environment override
        env_pref = _env_provider_preference()
        if provider == "auto" and env_pref != "auto":
            provider = env_pref
        # Do a quick availability check for the requested provider's client
        if provider == "valkey":
            try:
                import valkey  # type: ignore
            except Exception:
                logging.warning("[set_cache] Valkey client not installed — falling back to Redis if available")
                provider = "redis"
        if provider == "redis":
            try:
                import redis  # type: ignore
            except Exception:
                logging.warning("[set_cache] Redis client not installed — caching will be disabled")
                _cache_instance = False
                return False

        instance = create_cache(provider=provider, config=config, ttl=ttl, time_out=time_out)
        instance.connect()
        if instance.client is False:
            # Provider-specific connect logic may set client=False to indicate unusable
            _cache_instance = False
            return False
        _cache_instance = instance
        return True
    except Exception as e:
        logging.error(f"[set_cache] Could not instantiate cache: {e}")
        _cache_instance = False
        return False


def get_cache() -> Union[BaseCache, bool, None]:
    """Return the global cache instance, initializing it if necessary.

    Returns:
        - BaseCache instance when caching is initialized and available.
        - False when caching is disabled or initialization failed.
        - None only transiently (should not be returned long-term).
    """
    global _cache_instance
    if _cache_instance is None:
        set_cache()
    if _cache_instance is False or _cache_instance is None:
        return False
    return _cache_instance


def cache_get(input_data: Any, company_id: Optional[str] = None) -> Optional[Any]:
    """Retrieve a cached value for the given input key.

    Optional company_id enforces tenant isolation at key generation time.
    If caching is disabled (get_cache returns False) this returns None.
    """
    cache = get_cache()
    if cache is False:
        return None
    # Preserve backward compatibility: avoid passing company_id when None so
    # existing mocks/tests expecting the old signature still pass.
    if company_id is None:
        return cache.get(input_data)
    return cache.get(input_data, company_id=company_id)


def cache_set(input_data: Any, output_data: Any, ttl: Optional[int] = None, company_id: Optional[str] = None):
    """Store a value in cache for the given input key.

    Optional company_id adds tenant scoping. No-op when caching is disabled.
    """
    cache = get_cache()
    if cache is False:
        return
    if company_id is None:
        cache.set(input_data, output_data, ttl)
    else:
        cache.set(input_data, output_data, ttl, company_id=company_id)


def cache_clear_company(company_id: str):
    """Clear all cached entries for a specific company_id."""
    cache = get_cache()
    if cache is False:
        return
    clear_func = getattr(cache, "clear_company", None)
    if callable(clear_func):
        clear_func(company_id)


def cache_clear_global():
    """Clear all cached entries that are not associated with any company_id."""
    cache = get_cache()
    if cache is False:
        return
    clear_func = getattr(cache, "clear_global", None)
    if callable(clear_func):
        clear_func()


def cache_clear_all():
    """Clear all cached entries across all tenants and global keys."""
    cache = get_cache()
    if cache is False:
        return
    clear_func = getattr(cache, "clear_all", None)
    if callable(clear_func):
        clear_func()


def cache_delete(input_data: Any, company_id: Optional[str] = None) -> bool:
    """Delete cached data for the given input and optional company_id.
    
    Returns:
        True if key was deleted, False if key didn't exist or caching is disabled
    """
    cache = get_cache()
    if cache is False:
        return False
    delete_func = getattr(cache, "delete", None)
    if callable(delete_func):
        if company_id is None:
            return delete_func(input_data)
        return delete_func(input_data, company_id=company_id)
    return False


def cache_exists(input_data: Any, company_id: Optional[str] = None) -> bool:
    """Check if cached data exists for the given input and optional company_id.
    
    Returns:
        True if key exists, False if key doesn't exist or caching is disabled
    """
    cache = get_cache()
    if cache is False:
        return False
    exists_func = getattr(cache, "exists", None)
    if callable(exists_func):
        if company_id is None:
            return exists_func(input_data)
        return exists_func(input_data, company_id=company_id)
    return False


def get_cache_client():
    """Get direct access to the underlying cache client.
    
    Returns:
        The underlying cache client instance (e.g., Redis client) or None if disabled
    """
    cache = get_cache()
    if cache is False:
        return None
    get_client_func = getattr(cache, "get_client", None)
    if callable(get_client_func):
        return get_client_func()
    return None

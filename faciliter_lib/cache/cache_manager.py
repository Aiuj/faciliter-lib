# cache_manager.py
# Cache manager with support for Redis and Valkey providers
import os
from typing import Any, Optional, Literal, Union
import logging
from .base_cache import BaseCache
from .redis_cache import RedisCache
from .valkey_cache import ValkeyCache
from .redis_config import RedisConfig
from .valkey_config import ValkeyConfig

CacheProvider = Literal["redis", "valkey", "auto"]


def _env_provider_preference() -> CacheProvider:
    """Read environment-level preference for cache backend.

    - `CACHE_BACKEND` can be set to `redis`, `valkey`, or `auto` (default).
    """
    env = os.getenv("CACHE_BACKEND", "auto").lower()
    if env in ("redis", "valkey", "auto"):
        return env  # type: ignore[return-value]
    return "auto"


def create_cache(
    provider: CacheProvider = "auto",
    name: str = "",
    config: Optional[Union[RedisConfig, ValkeyConfig]] = None,
    ttl: Optional[int] = None,
    time_out: Optional[int] = None,
) -> BaseCache:
    """Create a cache instance based on the specified provider.

    The function supports:
    - explicit provider selection (`redis` or `valkey`)
    - `auto` selection which consults `CACHE_BACKEND` env vars
    - using a RedisConfig when Valkey is requested (Valkey is treated as a
      Redis-compatible drop-in and we convert configs where necessary)
    """
    if provider == "auto":
        provider = _env_provider_preference()
        # If still auto, fall back to auto-detection based on available envs
        if provider == "auto":
            provider = _auto_detect_provider()

    # If caller passed a RedisConfig but requested valkey, convert it
    if provider == "valkey" and isinstance(config, RedisConfig) and not isinstance(config, ValkeyConfig):
        # Cast by creating a ValkeyConfig from the RedisConfig values
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
    """Automatically detect which cache provider to use.

    Behavior:
    - Prefer Valkey by default in `auto` mode.
    - If the Valkey client library is not importable, fall back to Redis.
    - If neither Valkey nor Redis client libraries are installed, return
      a sentinel of 'redis' by convention but callers should detect client
      availability before using the cache; we also prevent initialization
      when no client is installed.
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
            # No cache client libraries installed — indicate no-cache by
            # returning 'auto' which will be interpreted by set_cache
            # as 'no client available'. We'll still return 'redis' as a
            # conventional value, but callers should check availability.
            return "redis"


_cache_instance = None


def set_cache(
    provider: CacheProvider = "auto",
    config: Optional[Union[RedisConfig, ValkeyConfig]] = None,
    ttl: Optional[int] = None,
    time_out: Optional[int] = None,
):
    """Explicitly initialize the global cache instance with custom parameters.

    Only creates a new instance if one does not already exist.
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
            _cache_instance = False
            return False
        _cache_instance = instance
        return True
    except Exception as e:
        logging.error(f"[set_cache] Could not instantiate cache: {e}")
        _cache_instance = False
        return False


def get_cache() -> Optional[BaseCache]:
    """Return the global cache instance if initialized."""
    global _cache_instance
    if _cache_instance is None:
        set_cache()
    if _cache_instance is False or _cache_instance is None:
        return False
    return _cache_instance


def cache_get(input_data: Any) -> Optional[Any]:
    """Get cached output for the given input data."""
    cache = get_cache()
    if cache is False:
        return None
    return cache.get(input_data)


def cache_set(input_data: Any, output_data: Any, ttl: Optional[int] = None):
    """Set cached output for the given input data."""
    cache = get_cache()
    if cache is False:
        return
    cache.set(input_data, output_data, ttl)

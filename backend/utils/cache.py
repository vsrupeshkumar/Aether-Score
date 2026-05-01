"""
Redis caching utilities
"""
import json
import os
from typing import Optional, Any, Callable
from functools import wraps
import redis
from utils.logger import get_logger
from utils.metrics import record_error

logger = get_logger(__name__)

# Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client for caching"""
    global _redis_client
    
    if _redis_client is None:
        cache_url = os.getenv("REDIS_CACHE_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/1")
        
        try:
            _redis_client = redis.from_url(
                cache_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis cache client connected", extra={"url": cache_url})
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}", extra={"error": str(e)})
            _redis_client = None
    
    return _redis_client


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from prefix and arguments"""
    key_parts = [prefix]
    
    # Add args
    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg))
        elif isinstance(arg, (list, dict)):
            key_parts.append(json.dumps(arg, sort_keys=True))
    
    # Add kwargs
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.append(json.dumps(dict(sorted_kwargs), sort_keys=True))
    
    return ":".join(key_parts)


def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    if not os.getenv("CACHE_ENABLED", "true").lower() == "true":
        return None
    
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Cache get error: {e}", extra={"key": key, "error": str(e)})
        return None


def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache with TTL"""
    if not os.getenv("CACHE_ENABLED", "true").lower() == "true":
        return False
    
    client = get_redis_client()
    if not client:
        return False
    
    try:
        serialized = json.dumps(value, default=str)
        client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.warning(f"Cache set error: {e}", extra={"key": key, "error": str(e)})
        return False


def delete_cache(key: str) -> bool:
    """Delete value from cache"""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete error: {e}", extra={"key": key, "error": str(e)})
        return False


def invalidate_pattern(pattern: str) -> int:
    """Invalidate all keys matching pattern"""
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache invalidate error: {e}", extra={"pattern": pattern, "error": str(e)})
        return 0


def cached(ttl: int = 3600, key_prefix: str = "cache"):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl=300, key_prefix="score")
        async def compute_score(address: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = get_cache(key)
            if cached_value is not None:
                return cached_value
            
            # Compute value
            result = await func(*args, **kwargs) if hasattr(func, '__call__') and hasattr(func, '__code__') else func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                set_cache(key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_score(wallet_address: str, score_data: dict, ttl: Optional[int] = None):
    """Cache score data for a wallet address"""
    if ttl is None:
        ttl = int(os.getenv("CACHE_TTL_SCORES", "3600"))
    
    key = cache_key("score", wallet_address)
    return set_cache(key, score_data, ttl)


def get_cached_score(wallet_address: str) -> Optional[dict]:
    """Get cached score for a wallet address"""
    key = cache_key("score", wallet_address)
    return get_cache(key)


def invalidate_score_cache(wallet_address: str):
    """Invalidate cached score for a wallet address"""
    key = cache_key("score", wallet_address)
    delete_cache(key)


def cache_rpc_result(method: str, params: dict, result: Any, ttl: Optional[int] = None):
    """Cache RPC call result"""
    if ttl is None:
        ttl = int(os.getenv("CACHE_TTL_RPC", "30"))
    
    key = cache_key("rpc", method, params)
    return set_cache(key, result, ttl)


def get_cached_rpc_result(method: str, params: dict) -> Optional[Any]:
    """Get cached RPC call result"""
    key = cache_key("rpc", method, params)
    return get_cache(key)


def cache_api_response(endpoint: str, params: dict, response: Any, ttl: Optional[int] = None):
    """Cache API response"""
    if ttl is None:
        ttl = int(os.getenv("CACHE_TTL_API", "300"))
    
    key = cache_key("api", endpoint, params)
    return set_cache(key, response, ttl)


def get_cached_api_response(endpoint: str, params: dict) -> Optional[Any]:
    """Get cached API response"""
    key = cache_key("api", endpoint, params)
    return get_cache(key)


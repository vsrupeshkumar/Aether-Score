"""
Cache middleware for API responses
"""
import hashlib
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from utils.cache import cache_api_response, get_cached_api_response, cache_key
from utils.logger import get_logger
from utils.metrics import record_error

logger = get_logger(__name__)

# Cacheable endpoints (GET requests only)
CACHEABLE_ENDPOINTS = [
    "/api/score/",
    "/api/staking/",
    "/api/lending/ltv/",
    "/api/oracle/price",
]


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching API responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check if endpoint is cacheable
        is_cacheable = any(request.url.path.startswith(endpoint) for endpoint in CACHEABLE_ENDPOINTS)
        if not is_cacheable:
            return await call_next(request)
        
        # Generate cache key from request
        cache_params = {
            "path": request.url.path,
            "query": str(request.query_params)
        }
        cache_key_str = cache_key("api", request.url.path, cache_params)
        
        # Try to get from cache
        cached_response = get_cached_api_response(request.url.path, cache_params)
        if cached_response is not None:
            logger.debug("Cache hit", extra={"endpoint": request.url.path})
            return Response(
                content=json.dumps(cached_response),
                media_type="application/json",
                headers={"X-Cache": "HIT"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses (200 OK)
        if response.status_code == 200:
            try:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Parse JSON if possible
                try:
                    response_data = json.loads(body.decode())
                    cache_api_response(request.url.path, cache_params, response_data)
                    logger.debug("Cached response", extra={"endpoint": request.url.path})
                except json.JSONDecodeError:
                    pass  # Don't cache non-JSON responses
                
                # Return response with cache header
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers={**dict(response.headers), "X-Cache": "MISS"},
                    media_type=response.media_type
                )
            except Exception as e:
                logger.warning(f"Cache middleware error: {e}", extra={"error": str(e)})
                return response
        
        return response


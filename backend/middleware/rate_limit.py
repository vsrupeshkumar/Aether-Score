"""
Rate limiting middleware
"""
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from typing import Callable

# Configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{RATE_LIMIT_PER_MINUTE}/minute", f"{RATE_LIMIT_PER_HOUR}/hour"],
    storage_uri=os.getenv("REDIS_URL"),  # Use Redis if available, otherwise in-memory
)

# Register rate limit exceeded handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    return _rate_limit_exceeded_handler(request, exc)


def get_user_identifier(request: Request) -> str:
    """
    Get user identifier for rate limiting
    Uses authenticated user address if available, otherwise IP address
    
    Args:
        request: FastAPI request object
        
    Returns:
        User identifier string
    """
    # If user is authenticated, use their address
    if hasattr(request.state, "authenticated") and request.state.authenticated:
        user_address = getattr(request.state, "user_address", None)
        if user_address:
            return f"user:{user_address}"
    
    # Otherwise use IP address
    return get_remote_address(request)


def rate_limit_user(limit: str) -> Callable:
    """
    Rate limit decorator using user identifier
    
    Args:
        limit: Rate limit string (e.g., "60/minute")
        
    Returns:
        Decorator function
    """
    return limiter.limit(limit, key_func=get_user_identifier)


"""
Role-Based Access Control (RBAC) middleware
"""
from fastapi import Request, HTTPException, status
from typing import List, Optional

# Role definitions
ROLES = {
    "user": 1,
    "service": 2,
    "admin": 3,
}

def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific roles
    
    Args:
        allowed_roles: List of allowed roles
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Get user role from request state
            user_role = getattr(request.state, "user_role", "user")
            
            # Check if user has required role
            if user_role not in allowed_roles:
                # Check role hierarchy
                user_role_level = ROLES.get(user_role, 0)
                required_level = max(ROLES.get(role, 0) for role in allowed_roles)
                
                if user_role_level < required_level:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
                    )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_admin(func):
    """Decorator to require admin role"""
    return require_role(["admin"])(func)


def require_service(func):
    """Decorator to require service role (for backend-to-backend calls)"""
    return require_role(["service", "admin"])(func)


def get_user_role(request: Request) -> str:
    """
    Get user role from request state
    
    Args:
        request: FastAPI request object
        
    Returns:
        User role (default: "user")
    """
    return getattr(request.state, "user_role", "user")


def is_admin(request: Request) -> bool:
    """
    Check if user is admin
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if user is admin
    """
    return get_user_role(request) == "admin"


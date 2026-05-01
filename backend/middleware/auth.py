"""
Authentication middleware
Supports both API keys and JWT tokens
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from utils.jwt_handler import verify_token
from utils.api_keys import validate_api_key, get_api_key_from_header

security = HTTPBearer(auto_error=False)

class AuthMiddleware:
    """Authentication middleware"""
    
    def __init__(self, require_auth: bool = True):
        """
        Initialize auth middleware
        
        Args:
            require_auth: Whether to require authentication (default: True)
        """
        self.require_auth = require_auth
    
    async def __call__(self, request: Request):
        """
        Authenticate request
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If authentication fails
        """
        if not self.require_auth:
            return
        
        # Try to get authorization header
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Try API key first
        api_key = get_api_key_from_header(authorization)
        if api_key and validate_api_key(api_key):
            # API key is valid
            request.state.auth_type = "api_key"
            request.state.authenticated = True
            return
        
        # Try JWT token
        try:
            credentials = HTTPAuthorizationCredentials(
                scheme="bearer",
                credentials=authorization.replace("Bearer ", "").replace("bearer ", "")
            )
            token = credentials.credentials
            payload = verify_token(token)
            
            if payload:
                request.state.auth_type = "jwt"
                request.state.authenticated = True
                request.state.user_address = payload.get("sub")
                request.state.user_role = payload.get("role", "user")
                return
        except Exception:
            pass
        
        # Authentication failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(request: Request) -> Optional[str]:
    """
    Get current authenticated user address from request state
    
    Args:
        request: FastAPI request object
        
    Returns:
        User address or None
    """
    if hasattr(request.state, "authenticated") and request.state.authenticated:
        return getattr(request.state, "user_address", None)
    return None


def get_current_role(request: Request) -> str:
    """
    Get current user role from request state
    
    Args:
        request: FastAPI request object
        
    Returns:
        User role (default: "user")
    """
    if hasattr(request.state, "authenticated") and request.state.authenticated:
        return getattr(request.state, "user_role", "user")
    return "user"


"""
API key authentication middleware for public API
"""
from typing import Optional
from fastapi import HTTPException, Request, status
from utils.logger import get_logger
from database.connection import get_db_session
from database.models import APIAccess
from sqlalchemy import select
import hashlib
from datetime import datetime

logger = get_logger(__name__)


async def get_api_key(request: Request) -> Optional[APIAccess]:
    """
    Get API key from request and validate
    
    Returns:
        APIAccess object if valid, None otherwise
    """
    try:
        # Get API key from header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not api_key:
            return None
        
        # Hash the API key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Look up API key in database
        async with get_db_session() as session:
            result = await session.execute(
                select(APIAccess).where(APIAccess.api_key == key_hash)
            )
            api_key_obj = result.scalar_one_or_none()
            
            if not api_key_obj:
                return None
            
            # Check if revoked
            if api_key_obj.revoked_at:
                return None
            
            # Check if expired
            if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
                return None
            
            # Update last used
            api_key_obj.last_used_at = datetime.utcnow()
            await session.commit()
            
            return api_key_obj
    except Exception as e:
        logger.error(f"Error validating API key: {e}", exc_info=True)
        return None


async def require_api_key(request: Request) -> APIAccess:
    """
    Require valid API key, raise exception if not present
    
    Returns:
        APIKey object
    """
    api_key = await get_api_key(request)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


"""
API access manager for third-party protocol access
"""
from typing import Dict, Optional, Any
import secrets
import hashlib
from datetime import datetime, timedelta
from utils.logger import get_logger
from database.connection import get_session
from database.models import APIAccess
from sqlalchemy import select

logger = get_logger(__name__)


class APIAccessManager:
    """Service for managing API access for third-party protocols"""
    
    API_KEY_LENGTH = 32
    
    def __init__(self):
        pass
    
    async def create_api_key(
        self,
        protocol_address: str,
        permissions: Optional[Dict[str, Any]] = None,
        rate_limit: int = 60,
        expires_in_days: Optional[int] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Create API key for protocol
        
        Args:
            protocol_address: Protocol address requesting access
            permissions: Optional permissions dict
            rate_limit: Requests per minute
            expires_in_days: Optional expiration days
            session: Database session (optional)
            
        Returns:
            API key info dict
        """
        try:
            # Generate API key
            api_key = self._generate_api_key()
            api_key_hash = self._hash_api_key(api_key)
            
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_api_key(
                        protocol_address, api_key, api_key_hash,
                        permissions, rate_limit, expires_at, db_session
                    )
            else:
                return await self._create_api_key(
                    protocol_address, api_key, api_key_hash,
                    permissions, rate_limit, expires_at, session
                )
        except Exception as e:
            logger.error(f"Error creating API key: {e}", exc_info=True)
            return None
    
    async def _create_api_key(
        self,
        protocol_address: str,
        api_key: str,
        api_key_hash: str,
        permissions: Optional[Dict[str, Any]],
        rate_limit: int,
        expires_at: Optional[datetime],
        session
    ) -> Optional[Dict[str, Any]]:
        """Create API key in database"""
        try:
            api_access = APIAccess(
                protocol_address=protocol_address,
                api_key=api_key_hash,
                permissions=permissions or {},
                rate_limit=rate_limit,
                expires_at=expires_at
            )
            session.add(api_access)
            await session.commit()
            await session.refresh(api_access)
            
            logger.info(f"Created API key for protocol {protocol_address}")
            
            return {
                "id": api_access.id,
                "protocol_address": protocol_address,
                "api_key": api_key,  # Return plaintext key only once
                "permissions": permissions or {},
                "rate_limit": rate_limit,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "created_at": api_access.created_at.isoformat() if api_access.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _create_api_key: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def validate_api_key(
        self,
        api_key: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Validate API key
        
        Args:
            api_key: API key to validate
            session: Database session (optional)
            
        Returns:
            API access info dict if valid, None otherwise
        """
        try:
            api_key_hash = self._hash_api_key(api_key)
            
            if session is None:
                async with get_session() as db_session:
                    return await self._validate_api_key(api_key_hash, db_session)
            else:
                return await self._validate_api_key(api_key_hash, session)
        except Exception as e:
            logger.error(f"Error validating API key: {e}", exc_info=True)
            return None
    
    async def _validate_api_key(
        self,
        api_key_hash: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Validate API key from database"""
        try:
            result = await session.execute(
                select(APIAccess).where(APIAccess.api_key == api_key_hash)
            )
            api_access = result.scalar_one_or_none()
            
            if not api_access:
                return None
            
            # Check if revoked
            if api_access.revoked_at:
                return None
            
            # Check if expired
            if api_access.expires_at and api_access.expires_at < datetime.utcnow():
                return None
            
            # Update last used
            api_access.last_used_at = datetime.utcnow()
            await session.commit()
            
            return {
                "id": api_access.id,
                "protocol_address": api_access.protocol_address,
                "permissions": api_access.permissions or {},
                "rate_limit": api_access.rate_limit,
            }
        except Exception as e:
            logger.error(f"Error in _validate_api_key: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def get_api_permissions(
        self,
        api_key: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Get permissions for API key
        
        Args:
            api_key: API key
            session: Database session (optional)
            
        Returns:
            Permissions dict
        """
        try:
            api_access_info = await self.validate_api_key(api_key, session)
            if not api_access_info:
                return None
            
            return api_access_info.get("permissions", {})
        except Exception as e:
            logger.error(f"Error getting API permissions: {e}", exc_info=True)
            return None
    
    async def revoke_api_key(
        self,
        api_key: str,
        session=None
    ) -> bool:
        """
        Revoke API key
        
        Args:
            api_key: API key to revoke
            session: Database session (optional)
            
        Returns:
            True if revoked successfully
        """
        try:
            api_key_hash = self._hash_api_key(api_key)
            
            if session is None:
                async with get_session() as db_session:
                    return await self._revoke_api_key(api_key_hash, db_session)
            else:
                return await self._revoke_api_key(api_key_hash, session)
        except Exception as e:
            logger.error(f"Error revoking API key: {e}", exc_info=True)
            return False
    
    async def _revoke_api_key(
        self,
        api_key_hash: str,
        session
    ) -> bool:
        """Revoke API key in database"""
        try:
            result = await session.execute(
                select(APIAccess).where(APIAccess.api_key == api_key_hash)
            )
            api_access = result.scalar_one_or_none()
            
            if not api_access:
                return False
            
            api_access.revoked_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Revoked API key for protocol {api_access.protocol_address}")
            return True
        except Exception as e:
            logger.error(f"Error in _revoke_api_key: {e}", exc_info=True)
            await session.rollback()
            return False
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(self.API_KEY_LENGTH)
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()


"""
Badge service for managing verification badges and calculating badge boosts
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class BadgeService:
    """Service for managing verification badges and calculating badge boosts"""
    
    # Badge type configurations
    BADGE_CONFIGS = {
        "community_verified": {
            "boost": 10,
            "description": "Community verified member",
        },
        "governance_participant": {
            "boost": 15,
            "description": "Active governance participant",
        },
        "early_adopter": {
            "boost": 20,
            "description": "Early adopter of AETHER-SCORE",
        },
        "liquidity_provider": {
            "boost": 15,
            "description": "Active liquidity provider",
        },
        "defi_expert": {
            "boost": 12,
            "description": "DeFi expert",
        },
        "nft_collector": {
            "boost": 8,
            "description": "NFT collector",
        },
        "gaming_enthusiast": {
            "boost": 8,
            "description": "Gaming enthusiast",
        },
    }
    
    # Maximum total badge boost
    MAX_TOTAL_BADGE_BOOST = 100
    
    async def issue_badge(
        self,
        address: str,
        badge_type: str,
        issuer: str,
        score_boost: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Issue a verification badge
        
        Args:
            address: Wallet address
            badge_type: Type of badge
            issuer: Who is issuing the badge
            score_boost: Custom boost (uses default if None)
            expires_at: Expiration date (None for permanent)
            metadata: Additional badge metadata
            session: Database session (optional)
            
        Returns:
            Badge dict if issued successfully
        """
        try:
            from database.connection import get_session
            from database.models import VerificationBadge
            
            if session is None:
                async with get_session() as db_session:
                    return await self._issue_badge(
                        address, badge_type, issuer, score_boost, expires_at, metadata, db_session
                    )
            else:
                return await self._issue_badge(
                    address, badge_type, issuer, score_boost, expires_at, metadata, session
                )
        except Exception as e:
            logger.error(f"Error issuing badge: {e}", exc_info=True)
            return None
    
    async def _issue_badge(
        self,
        address: str,
        badge_type: str,
        issuer: str,
        score_boost: Optional[int],
        expires_at: Optional[datetime],
        metadata: Optional[Dict[str, Any]],
        session
    ) -> Optional[Dict[str, Any]]:
        """Issue badge in database"""
        from database.models import VerificationBadge
        
        try:
            # Validate badge type
            if badge_type not in self.BADGE_CONFIGS:
                logger.warning(f"Invalid badge type: {badge_type}")
                return None
            
            # Use default boost if not provided
            if score_boost is None:
                score_boost = self.BADGE_CONFIGS[badge_type]["boost"]
            
            # Create badge
            badge = VerificationBadge(
                wallet_address=address,
                badge_type=badge_type,
                issuer=issuer,
                score_boost=score_boost,
                expires_at=expires_at,
                metadata=metadata or {}
            )
            session.add(badge)
            await session.commit()
            
            logger.info(f"Issued {badge_type} badge to {address} by {issuer}")
            
            return {
                "id": badge.id,
                "badge_type": badge_type,
                "issuer": issuer,
                "score_boost": score_boost,
                "expires_at": badge.expires_at.isoformat() if badge.expires_at else None,
                "created_at": badge.created_at.isoformat() if badge.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _issue_badge: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def revoke_badge(
        self,
        badge_id: int,
        session=None
    ) -> bool:
        """
        Revoke a badge
        
        Args:
            badge_id: Badge ID
            session: Database session (optional)
            
        Returns:
            True if revoked successfully
        """
        try:
            from database.connection import get_session
            from database.models import VerificationBadge
            from sqlalchemy import select, delete
            
            if session is None:
                async with get_session() as db_session:
                    return await self._revoke_badge(badge_id, db_session)
            else:
                return await self._revoke_badge(badge_id, session)
        except Exception as e:
            logger.error(f"Error revoking badge: {e}", exc_info=True)
            return False
    
    async def _revoke_badge(self, badge_id: int, session) -> bool:
        """Revoke badge from database"""
        from database.models import VerificationBadge
        from sqlalchemy import select, delete
        
        try:
            result = await session.execute(
                delete(VerificationBadge).where(VerificationBadge.id == badge_id)
            )
            await session.commit()
            
            if result.rowcount > 0:
                logger.info(f"Revoked badge {badge_id}")
                return True
            else:
                logger.warning(f"Badge not found: {badge_id}")
                return False
        except Exception as e:
            logger.error(f"Error in _revoke_badge: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def get_active_badges(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get all active badges for an address
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of active badge dicts
        """
        try:
            from database.connection import get_session
            from database.models import VerificationBadge
            from sqlalchemy import select
            from datetime import datetime
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_active_badges(address, db_session)
            else:
                return await self._get_active_badges(address, session)
        except Exception as e:
            logger.error(f"Error getting active badges: {e}", exc_info=True)
            return []
    
    async def _get_active_badges(self, address: str, session) -> List[Dict[str, Any]]:
        """Get active badges from database"""
        from database.models import VerificationBadge
        from sqlalchemy import select
        from datetime import datetime
        
        try:
            now = datetime.utcnow()
            
            result = await session.execute(
                select(VerificationBadge)
                .where(VerificationBadge.wallet_address == address)
                .where(
                    (VerificationBadge.expires_at.is_(None)) |
                    (VerificationBadge.expires_at > now)
                )
            )
            badges = result.scalars().all()
            
            return [
                {
                    "id": badge.id,
                    "badge_type": badge.badge_type,
                    "issuer": badge.issuer,
                    "score_boost": badge.score_boost,
                    "expires_at": badge.expires_at.isoformat() if badge.expires_at else None,
                    "metadata": badge.extra_metadata or {},
                    "created_at": badge.created_at.isoformat() if badge.created_at else None,
                }
                for badge in badges
            ]
        except Exception as e:
            logger.error(f"Error in _get_active_badges: {e}", exc_info=True)
            return []
    
    async def calculate_badge_boost(
        self,
        address: str,
        session=None
    ) -> int:
        """
        Calculate total badge boost for an address
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Total badge boost (capped at MAX_TOTAL_BADGE_BOOST)
        """
        try:
            badges = await self.get_active_badges(address, session)
            total_boost = sum(badge["score_boost"] for badge in badges)
            return min(total_boost, self.MAX_TOTAL_BADGE_BOOST)
        except Exception as e:
            logger.error(f"Error calculating badge boost: {e}", exc_info=True)
            return 0



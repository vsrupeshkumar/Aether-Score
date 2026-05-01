"""
Referral service for managing user referrals and calculating referral boosts
"""
import secrets
import string
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class ReferralService:
    """Service for managing referrals and calculating referral boosts"""
    
    # Referral boost configuration
    BOOST_PER_REFERRAL = 5  # Points per active referral
    MAX_REFERRAL_BOOST = 50  # Maximum boost from referrals
    REFERRAL_CODE_LENGTH = 8
    
    def generate_referral_code(self, address: str) -> str:
        """
        Generate unique referral code for an address
        
        Args:
            address: Wallet address
            
        Returns:
            Unique referral code
        """
        # Use first 4 chars of address + random string
        prefix = address[2:6].upper()  # Skip '0x'
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) 
                             for _ in range(self.REFERRAL_CODE_LENGTH - 4))
        return f"{prefix}{random_part}"
    
    async def create_referral(
        self,
        referrer_address: str,
        referral_code: Optional[str] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a referral code for an address
        
        Args:
            referrer_address: Address creating the referral
            referral_code: Optional custom code (otherwise auto-generated)
            session: Database session (optional)
            
        Returns:
            Referral dict with code
        """
        try:
            from database.connection import get_session
            from database.models import Referral
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_referral(referrer_address, referral_code, db_session)
            else:
                return await self._create_referral(referrer_address, referral_code, session)
        except Exception as e:
            logger.error(f"Error creating referral: {e}", exc_info=True)
            return None
    
    async def _create_referral(
        self,
        referrer_address: str,
        referral_code: Optional[str],
        session
    ) -> Optional[Dict[str, Any]]:
        """Create referral in database"""
        from database.models import Referral
        from sqlalchemy import select
        
        try:
            # Generate code if not provided
            if not referral_code:
                referral_code = self.generate_referral_code(referrer_address)
            
            # Check if code already exists
            result = await session.execute(
                select(Referral)
                .where(Referral.referral_code == referral_code)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Regenerate if collision
                referral_code = self.generate_referral_code(referrer_address)
            
            # Create referral
            referral = Referral(
                referrer_address=referrer_address,
                referral_code=referral_code,
                status='pending'
            )
            session.add(referral)
            await session.commit()
            
            return {
                "id": referral.id,
                "referral_code": referral_code,
                "referrer_address": referrer_address,
                "status": referral.status,
                "created_at": referral.created_at.isoformat() if referral.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _create_referral: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def activate_referral(
        self,
        referral_code: str,
        referred_address: str,
        session=None
    ) -> bool:
        """
        Activate a referral by linking it to a referred address
        
        Args:
            referral_code: Referral code
            referred_address: Address being referred
            session: Database session (optional)
            
        Returns:
            True if activated successfully
        """
        try:
            from database.connection import get_session
            from database.models import Referral
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._activate_referral(referral_code, referred_address, db_session)
            else:
                return await self._activate_referral(referral_code, referred_address, session)
        except Exception as e:
            logger.error(f"Error activating referral: {e}", exc_info=True)
            return False
    
    async def _activate_referral(
        self,
        referral_code: str,
        referred_address: str,
        session
    ) -> bool:
        """Activate referral in database"""
        from database.models import Referral
        from sqlalchemy import select
        
        try:
            # Find referral
            result = await session.execute(
                select(Referral)
                .where(Referral.referral_code == referral_code)
            )
            referral = result.scalar_one_or_none()
            
            if not referral:
                logger.warning(f"Referral code not found: {referral_code}")
                return False
            
            if referral.status != 'pending':
                logger.warning(f"Referral already activated: {referral_code}")
                return False
            
            if referral.referrer_address.lower() == referred_address.lower():
                logger.warning("Cannot refer yourself")
                return False
            
            # Check if address already referred
            existing_result = await session.execute(
                select(Referral)
                .where(Referral.referred_address == referred_address)
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                logger.warning(f"Address already referred: {referred_address}")
                return False
            
            # Activate referral
            referral.referred_address = referred_address
            referral.status = 'active'
            referral.activated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Activated referral {referral_code} for {referred_address}")
            return True
        except Exception as e:
            logger.error(f"Error in _activate_referral: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def calculate_referral_boost(
        self,
        referrer_address: str,
        session=None
    ) -> int:
        """
        Calculate referral boost for an address
        
        Args:
            referrer_address: Address to calculate boost for
            session: Database session (optional)
            
        Returns:
            Referral boost points (0-50)
        """
        try:
            from database.connection import get_session
            from database.models import Referral
            from sqlalchemy import select, func
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_boost(referrer_address, db_session)
            else:
                return await self._calculate_boost(referrer_address, session)
        except Exception as e:
            logger.error(f"Error calculating referral boost: {e}", exc_info=True)
            return 0
    
    async def _calculate_boost(self, referrer_address: str, session) -> int:
        """Calculate boost from referrals"""
        from database.models import Referral
        from sqlalchemy import select
        
        try:
            # Count active referrals
            result = await session.execute(
                select(Referral)
                .where(
                    Referral.referrer_address == referrer_address,
                    Referral.status == 'active'
                )
            )
            active_referrals = result.scalars().all()
            
            # Calculate boost
            boost = len(active_referrals) * self.BOOST_PER_REFERRAL
            return min(boost, self.MAX_REFERRAL_BOOST)
        except Exception as e:
            logger.error(f"Error in _calculate_boost: {e}", exc_info=True)
            return 0
    
    async def get_referral_stats(
        self,
        address: str,
        session=None
    ) -> Dict[str, Any]:
        """
        Get referral statistics for an address
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Referral statistics
        """
        try:
            from database.connection import get_session
            from database.models import Referral
            from sqlalchemy import select, func
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_stats(address, db_session)
            else:
                return await self._get_stats(address, session)
        except Exception as e:
            logger.error(f"Error getting referral stats: {e}", exc_info=True)
            return {}
    
    async def _get_stats(self, address: str, session) -> Dict[str, Any]:
        """Get referral statistics"""
        from database.models import Referral
        from sqlalchemy import select, func
        
        try:
            # Get referrals created by this address
            referrer_result = await session.execute(
                select(Referral)
                .where(Referral.referrer_address == address)
            )
            referrals = referrer_result.scalars().all()
            
            # Count by status
            pending = sum(1 for r in referrals if r.status == 'pending')
            active = sum(1 for r in referrals if r.status == 'active')
            completed = sum(1 for r in referrals if r.status == 'completed')
            
            # Get referral code
            referral_code = None
            for r in referrals:
                if r.status == 'pending' or r.status == 'active':
                    referral_code = r.referral_code
                    break
            
            return {
                "referral_code": referral_code,
                "total_referrals": len(referrals),
                "pending": pending,
                "active": active,
                "completed": completed,
                "boost": await self._calculate_boost(address, session),
            }
        except Exception as e:
            logger.error(f"Error in _get_stats: {e}", exc_info=True)
            return {}


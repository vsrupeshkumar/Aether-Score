"""
Referral rewards service for calculating and tracking NCRD token rewards
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from services.referral_service import ReferralService
from services.scoring import ScoringService

logger = get_logger(__name__)


class ReferralRewardsService:
    """Service for managing referral rewards"""
    
    # Reward amounts in NCRD
    REFERRER_REWARD = Decimal('50')  # NCRD per successful referral
    REFERRED_REWARD = Decimal('25')  # NCRD bonus for using referral code
    MILESTONE_REWARDS = {
        500: Decimal('10'),   # 10 NCRD for reaching 500
        600: Decimal('15'),   # 15 NCRD for reaching 600
        700: Decimal('20'),   # 20 NCRD for reaching 700
        800: Decimal('30'),   # 30 NCRD for reaching 800
        900: Decimal('50'),   # 50 NCRD for reaching 900
    }
    
    def __init__(self):
        self.referral_service = ReferralService()
        self.scoring_service = ScoringService()
    
    async def calculate_referrer_reward(
        self,
        referrer_address: str,
        referred_address: str,
        session=None
    ) -> Decimal:
        """
        Calculate NCRD reward for referrer
        
        Args:
            referrer_address: Address of referrer
            referred_address: Address of referred user
            session: Database session (optional)
            
        Returns:
            Reward amount in NCRD
        """
        try:
            # Check if referred user has generated a score
            score_result = await self.scoring_service.compute_score(referred_address)
            has_score = score_result.get('score', 0) > 0
            
            if not has_score:
                return Decimal('0')
            
            # Check if referral is active
            from database.connection import get_session
            from database.models import Referral
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_referrer_reward(referrer_address, referred_address, db_session)
            else:
                return await self._calculate_referrer_reward(referrer_address, referred_address, session)
        except Exception as e:
            logger.error(f"Error calculating referrer reward: {e}", exc_info=True)
            return Decimal('0')
    
    async def _calculate_referrer_reward(
        self,
        referrer_address: str,
        referred_address: str,
        session
    ) -> Decimal:
        """Calculate referrer reward from database"""
        from database.models import Referral, ReferralReward
        from sqlalchemy import select
        
        try:
            # Find active referral
            result = await session.execute(
                select(Referral).where(
                    Referral.referrer_address == referrer_address,
                    Referral.referred_address == referred_address,
                    Referral.status == 'active'
                )
            )
            referral = result.scalar_one_or_none()
            
            if not referral:
                return Decimal('0')
            
            # Check if reward already given
            reward_result = await session.execute(
                select(ReferralReward).where(
                    ReferralReward.referral_id == referral.id,
                    ReferralReward.recipient_address == referrer_address,
                    ReferralReward.reward_type == 'referrer',
                    ReferralReward.status == 'distributed'
                )
            )
            existing_reward = reward_result.scalar_one_or_none()
            
            if existing_reward:
                return Decimal('0')  # Already rewarded
            
            return self.REFERRER_REWARD
        except Exception as e:
            logger.error(f"Error in _calculate_referrer_reward: {e}", exc_info=True)
            return Decimal('0')
    
    async def calculate_referred_reward(
        self,
        referred_address: str,
        session=None
    ) -> Decimal:
        """
        Calculate NCRD reward for referred user
        
        Args:
            referred_address: Address of referred user
            session: Database session (optional)
            
        Returns:
            Reward amount in NCRD
        """
        try:
            # Check if user used a referral code
            from database.connection import get_session
            from database.models import Referral
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_referred_reward(referred_address, db_session)
            else:
                return await self._calculate_referred_reward(referred_address, session)
        except Exception as e:
            logger.error(f"Error calculating referred reward: {e}", exc_info=True)
            return Decimal('0')
    
    async def _calculate_referred_reward(
        self,
        referred_address: str,
        session
    ) -> Decimal:
        """Calculate referred reward from database"""
        from database.models import Referral, ReferralReward
        from sqlalchemy import select
        
        try:
            # Find referral for this address
            result = await session.execute(
                select(Referral).where(
                    Referral.referred_address == referred_address,
                    Referral.status == 'active'
                )
            )
            referral = result.scalar_one_or_none()
            
            if not referral:
                return Decimal('0')
            
            # Check if reward already given
            reward_result = await session.execute(
                select(ReferralReward).where(
                    ReferralReward.referral_id == referral.id,
                    ReferralReward.recipient_address == referred_address,
                    ReferralReward.reward_type == 'referred',
                    ReferralReward.status == 'distributed'
                )
            )
            existing_reward = reward_result.scalar_one_or_none()
            
            if existing_reward:
                return Decimal('0')  # Already rewarded
            
            return self.REFERRED_REWARD
        except Exception as e:
            logger.error(f"Error in _calculate_referred_reward: {e}", exc_info=True)
            return Decimal('0')
    
    async def calculate_milestone_reward(
        self,
        address: str,
        score: int,
        session=None
    ) -> Decimal:
        """
        Calculate milestone reward based on score
        
        Args:
            address: Wallet address
            score: Current score
            session: Database session (optional)
            
        Returns:
            Milestone reward amount in NCRD
        """
        try:
            # Find highest milestone reached
            milestone_reward = Decimal('0')
            milestone_score = 0
            
            for milestone, reward in sorted(self.MILESTONE_REWARDS.items()):
                if score >= milestone:
                    milestone_reward = reward
                    milestone_score = milestone
            
            if milestone_reward == 0:
                return Decimal('0')
            
            # Check if milestone reward already given
            from database.connection import get_session
            from database.models import ReferralReward
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._check_milestone_reward(address, milestone_score, milestone_reward, db_session)
            else:
                return await self._check_milestone_reward(address, milestone_score, milestone_reward, session)
        except Exception as e:
            logger.error(f"Error calculating milestone reward: {e}", exc_info=True)
            return Decimal('0')
    
    async def _check_milestone_reward(
        self,
        address: str,
        milestone_score: int,
        reward_amount: Decimal,
        session
    ) -> Decimal:
        """Check if milestone reward already given"""
        from database.models import ReferralReward
        from sqlalchemy import select
        
        try:
            # Check if this milestone was already rewarded
            result = await session.execute(
                select(ReferralReward).where(
                    ReferralReward.recipient_address == address,
                    ReferralReward.reward_type == 'milestone',
                    ReferralReward.status == 'distributed'
                )
            )
            existing_rewards = result.scalars().all()
            
            # Check metadata for milestone score
            for reward in existing_rewards:
                metadata = reward.extra_metadata or {}
                if metadata.get('milestone_score') == milestone_score:
                    return Decimal('0')  # Already rewarded
            
            return reward_amount
        except Exception as e:
            logger.error(f"Error in _check_milestone_reward: {e}", exc_info=True)
            return Decimal('0')
    
    async def track_referral_reward(
        self,
        referral_id: int,
        recipient_address: str,
        reward_type: str,
        amount: Decimal,
        metadata: Optional[Dict[str, Any]] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Track pending reward
        
        Args:
            referral_id: Referral ID
            recipient_address: Recipient address
            reward_type: Reward type ('referrer', 'referred', 'milestone')
            amount: Reward amount
            metadata: Optional metadata
            session: Database session (optional)
            
        Returns:
            Created reward dict
        """
        try:
            from database.connection import get_session
            from database.models import ReferralReward
            
            if session is None:
                async with get_session() as db_session:
                    return await self._track_referral_reward(
                        referral_id, recipient_address, reward_type, amount, metadata, db_session
                    )
            else:
                return await self._track_referral_reward(
                    referral_id, recipient_address, reward_type, amount, metadata, session
                )
        except Exception as e:
            logger.error(f"Error tracking referral reward: {e}", exc_info=True)
            return None
    
    async def _track_referral_reward(
        self,
        referral_id: int,
        recipient_address: str,
        reward_type: str,
        amount: Decimal,
        metadata: Optional[Dict[str, Any]],
        session
    ) -> Optional[Dict[str, Any]]:
        """Track reward in database"""
        from database.models import ReferralReward
        
        try:
            reward = ReferralReward(
                referral_id=referral_id,
                recipient_address=recipient_address,
                reward_type=reward_type,
                amount_ncrd=amount,
                status='pending',
                metadata=metadata or {}
            )
            session.add(reward)
            await session.commit()
            
            logger.info(f"Tracked {reward_type} reward of {amount} NCRD for {recipient_address}")
            
            return {
                "id": reward.id,
                "referral_id": referral_id,
                "recipient_address": recipient_address,
                "reward_type": reward_type,
                "amount_ncrd": float(amount),
                "status": "pending",
                "created_at": reward.created_at.isoformat() if reward.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _track_referral_reward: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def get_pending_rewards(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get pending rewards for address
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of pending reward dicts
        """
        try:
            from database.connection import get_session
            from database.models import ReferralReward
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_pending_rewards(address, db_session)
            else:
                return await self._get_pending_rewards(address, session)
        except Exception as e:
            logger.error(f"Error getting pending rewards: {e}", exc_info=True)
            return []
    
    async def _get_pending_rewards(
        self,
        address: str,
        session
    ) -> List[Dict[str, Any]]:
        """Get pending rewards from database"""
        from database.models import ReferralReward
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(ReferralReward).where(
                    ReferralReward.recipient_address == address,
                    ReferralReward.status == 'pending'
                ).order_by(ReferralReward.created_at.desc())
            )
            rewards = result.scalars().all()
            
            return [
                {
                    "id": reward.id,
                    "referral_id": reward.referral_id,
                    "reward_type": reward.reward_type,
                    "amount_ncrd": float(reward.amount_ncrd),
                    "status": reward.status,
                    "created_at": reward.created_at.isoformat() if reward.created_at else None,
                    "metadata": reward.extra_metadata or {},
                }
                for reward in rewards
            ]
        except Exception as e:
            logger.error(f"Error in _get_pending_rewards: {e}", exc_info=True)
            return []


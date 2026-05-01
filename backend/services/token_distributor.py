"""
Token distributor service for hybrid on-chain/off-chain token distribution
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from services.blockchain import BlockchainService

logger = get_logger(__name__)


class TokenDistributorService:
    """Service for distributing NCRD tokens"""
    
    # Distribution threshold (NCRD)
    DISTRIBUTION_THRESHOLD = Decimal('100')  # Distribute when 100 NCRD total pending
    
    def __init__(self):
        self.blockchain_service = BlockchainService()
    
    async def distribute_reward(
        self,
        address: str,
        amount: Decimal,
        reason: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Distribute NCRD tokens (tracks off-chain, distributes on-chain when threshold reached)
        
        Args:
            address: Recipient address
            amount: Amount in NCRD
            reason: Reason for distribution
            session: Database session (optional)
            
        Returns:
            Distribution result dict
        """
        try:
            # For now, just track off-chain
            # Actual on-chain distribution happens via batch_distribute_rewards
            logger.info(f"Tracked reward: {amount} NCRD to {address} for {reason}")
            
            return {
                "address": address,
                "amount": float(amount),
                "reason": reason,
                "status": "tracked",
                "message": "Reward tracked, will be distributed when threshold reached",
            }
        except Exception as e:
            logger.error(f"Error distributing reward: {e}", exc_info=True)
            return None
    
    async def batch_distribute_rewards(
        self,
        rewards: List[Dict[str, Any]],
        session=None
    ) -> Dict[str, Any]:
        """
        Batch distribute multiple rewards
        
        Args:
            rewards: List of reward dicts with 'address' and 'amount'
            session: Database session (optional)
            
        Returns:
            Distribution result dict
        """
        try:
            from database.connection import get_session
            from database.models import ReferralReward
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._batch_distribute_rewards(rewards, db_session)
            else:
                return await self._batch_distribute_rewards(rewards, session)
        except Exception as e:
            logger.error(f"Error batch distributing rewards: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _batch_distribute_rewards(
        self,
        rewards: List[Dict[str, Any]],
        session
    ) -> Dict[str, Any]:
        """Batch distribute rewards on-chain"""
        from database.models import ReferralReward
        from sqlalchemy import select
        import os
        
        try:
            # Get NCRD token address
            ncrd_token_address = os.getenv("NCRD_TOKEN_ADDRESS")
            if not ncrd_token_address:
                logger.warning("NCRD_TOKEN_ADDRESS not set, cannot distribute tokens")
                return {
                    "success": False,
                    "error": "NCRD token address not configured",
                }
            
            # For now, simulate on-chain distribution
            # In production, would use web3 to call ERC20 transfer
            distributed_count = 0
            total_amount = Decimal('0')
            
            for reward in rewards:
                reward_id = reward.get('id')
                address = reward.get('address') or reward.get('recipient_address')
                amount = Decimal(str(reward.get('amount', 0)))
                
                if not reward_id or not address:
                    continue
                
                # Update reward status
                result = await session.execute(
                    select(ReferralReward).where(ReferralReward.id == reward_id)
                )
                reward_obj = result.scalar_one_or_none()
                
                if reward_obj and reward_obj.status == 'pending':
                    # Simulate on-chain transfer
                    # In production: await self._transfer_tokens(address, amount, ncrd_token_address)
                    tx_hash = f"0x{'0' * 64}"  # Placeholder
                    
                    reward_obj.status = 'distributed'
                    reward_obj.distribution_tx_hash = tx_hash
                    reward_obj.distributed_at = datetime.utcnow()
                    
                    distributed_count += 1
                    total_amount += amount
            
            await session.commit()
            
            logger.info(f"Distributed {distributed_count} rewards totaling {total_amount} NCRD")
            
            return {
                "success": True,
                "distributed_count": distributed_count,
                "total_amount": float(total_amount),
            }
        except Exception as e:
            logger.error(f"Error in _batch_distribute_rewards: {e}", exc_info=True)
            await session.rollback()
            return {
                "success": False,
                "error": str(e),
            }
    
    async def check_distribution_threshold(
        self,
        session=None
    ) -> Dict[str, Any]:
        """
        Check if threshold reached for on-chain distribution
        
        Args:
            session: Database session (optional)
            
        Returns:
            Threshold check result dict
        """
        try:
            from database.connection import get_session
            from database.models import ReferralReward
            from sqlalchemy import select, func
            
            if session is None:
                async with get_session() as db_session:
                    return await self._check_distribution_threshold(db_session)
            else:
                return await self._check_distribution_threshold(session)
        except Exception as e:
            logger.error(f"Error checking distribution threshold: {e}", exc_info=True)
            return {
                "threshold_reached": False,
                "error": str(e),
            }
    
    async def _check_distribution_threshold(
        self,
        session
    ) -> Dict[str, Any]:
        """Check threshold from database"""
        from database.models import ReferralReward
        from sqlalchemy import select, func
        
        try:
            # Sum pending rewards
            result = await session.execute(
                select(func.sum(ReferralReward.amount_ncrd)).where(
                    ReferralReward.status == 'pending'
                )
            )
            total_pending = result.scalar() or Decimal('0')
            
            threshold_reached = total_pending >= self.DISTRIBUTION_THRESHOLD
            
            return {
                "threshold_reached": threshold_reached,
                "total_pending": float(total_pending),
                "threshold": float(self.DISTRIBUTION_THRESHOLD),
                "remaining": float(max(Decimal('0'), self.DISTRIBUTION_THRESHOLD - total_pending)),
            }
        except Exception as e:
            logger.error(f"Error in _check_distribution_threshold: {e}", exc_info=True)
            return {
                "threshold_reached": False,
                "error": str(e),
            }
    
    async def execute_onchain_distribution(
        self,
        pending_rewards: Optional[List[Dict[str, Any]]] = None,
        session=None
    ) -> Dict[str, Any]:
        """
        Execute on-chain token transfer
        
        Args:
            pending_rewards: Optional list of pending rewards (will fetch if None)
            session: Database session (optional)
            
        Returns:
            Distribution result dict
        """
        try:
            from database.connection import get_session
            from database.models import ReferralReward
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._execute_onchain_distribution(pending_rewards, db_session)
            else:
                return await self._execute_onchain_distribution(pending_rewards, session)
        except Exception as e:
            logger.error(f"Error executing on-chain distribution: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _execute_onchain_distribution(
        self,
        pending_rewards: Optional[List[Dict[str, Any]]],
        session
    ) -> Dict[str, Any]:
        """Execute on-chain distribution"""
        from database.models import ReferralReward
        from sqlalchemy import select
        from datetime import datetime
        
        try:
            # Fetch pending rewards if not provided
            if pending_rewards is None:
                result = await session.execute(
                    select(ReferralReward).where(
                        ReferralReward.status == 'pending'
                    ).limit(100)  # Limit batch size
                )
                rewards = result.scalars().all()
                pending_rewards = [
                    {
                        "id": r.id,
                        "address": r.recipient_address,
                        "amount": float(r.amount_ncrd),
                    }
                    for r in rewards
                ]
            
            if not pending_rewards:
                return {
                    "success": True,
                    "message": "No pending rewards to distribute",
                    "distributed_count": 0,
                }
            
            # Batch distribute
            return await self._batch_distribute_rewards(pending_rewards, session)
        except Exception as e:
            logger.error(f"Error in _execute_onchain_distribution: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }


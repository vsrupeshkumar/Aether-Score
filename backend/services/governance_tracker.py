"""
Governance tracker service for tracking DAO participation and calculating reputation scores
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class GovernanceTracker:
    """Service for tracking governance participation and calculating reputation scores"""
    
    # Known governance protocols (can be extended)
    GOVERNANCE_PROTOCOLS = {
        "Uniswap": {
            "governance_contract": "0x408ED6354d4973f66138C91495F2f2FCbd8724C3",  # Uniswap Governor
            "chain_id": 1,
        },
        "Aave": {
            "governance_contract": "0xEC568fffba86c094cf06b22134B23074DFE2252c",  # Aave Governor
            "chain_id": 1,
        },
        "Compound": {
            "governance_contract": "0xc0Da02939E1441F49763C5dC0C1C5C0C5C5C5C5C5",  # Placeholder
            "chain_id": 1,
        },
    }
    
    # Score boost per activity type
    ACTIVITY_SCORES = {
        "vote": 5,  # Points per vote
        "proposal": 25,  # Points per proposal created
        "delegation": 10,  # Points for delegating
        "delegate": 15,  # Points for being delegated to
    }
    
    # Maximum governance score boost
    MAX_GOVERNANCE_SCORE = 100
    
    async def track_vote(
        self,
        address: str,
        protocol: str,
        proposal_id: str,
        tx_hash: str,
        chain_id: int,
        session=None
    ) -> bool:
        """
        Track voting activity
        
        Args:
            address: Wallet address
            protocol: Protocol name (e.g., "Uniswap")
            proposal_id: Proposal identifier
            tx_hash: Transaction hash
            chain_id: Chain ID
            session: Database session (optional)
            
        Returns:
            True if tracked successfully
        """
        try:
            from database.connection import get_session
            from database.models import GovernanceActivity
            
            if session is None:
                async with get_session() as db_session:
                    return await self._track_activity(
                        address, protocol, 'vote', proposal_id, tx_hash, chain_id, db_session
                    )
            else:
                return await self._track_activity(
                    address, protocol, 'vote', proposal_id, tx_hash, chain_id, session
                )
        except Exception as e:
            logger.error(f"Error tracking vote: {e}", exc_info=True)
            return False
    
    async def track_proposal(
        self,
        address: str,
        protocol: str,
        proposal_id: str,
        tx_hash: str,
        chain_id: int,
        session=None
    ) -> bool:
        """
        Track proposal creation
        
        Args:
            address: Wallet address
            protocol: Protocol name
            proposal_id: Proposal identifier
            tx_hash: Transaction hash
            chain_id: Chain ID
            session: Database session (optional)
            
        Returns:
            True if tracked successfully
        """
        try:
            from database.connection import get_session
            
            if session is None:
                async with get_session() as db_session:
                    return await self._track_activity(
                        address, protocol, 'proposal', proposal_id, tx_hash, chain_id, db_session
                    )
            else:
                return await self._track_activity(
                    address, protocol, 'proposal', proposal_id, tx_hash, chain_id, session
                )
        except Exception as e:
            logger.error(f"Error tracking proposal: {e}", exc_info=True)
            return False
    
    async def track_delegation(
        self,
        address: str,
        protocol: str,
        delegate_to: str,
        tx_hash: str,
        chain_id: int,
        session=None
    ) -> bool:
        """
        Track delegation activity
        
        Args:
            address: Wallet address (delegator)
            protocol: Protocol name
            delegate_to: Address being delegated to
            tx_hash: Transaction hash
            chain_id: Chain ID
            session: Database session (optional)
            
        Returns:
            True if tracked successfully
        """
        try:
            from database.connection import get_session
            
            if session is None:
                async with get_session() as db_session:
                    return await self._track_activity(
                        address, protocol, 'delegation', None, tx_hash, chain_id, db_session,
                        metadata={"delegate_to": delegate_to}
                    )
            else:
                return await self._track_activity(
                    address, protocol, 'delegation', None, tx_hash, chain_id, session,
                    metadata={"delegate_to": delegate_to}
                )
        except Exception as e:
            logger.error(f"Error tracking delegation: {e}", exc_info=True)
            return False
    
    async def _track_activity(
        self,
        address: str,
        protocol: str,
        activity_type: str,
        proposal_id: Optional[str],
        tx_hash: str,
        chain_id: int,
        session,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track governance activity"""
        from database.models import GovernanceActivity
        from sqlalchemy import select
        
        try:
            # Check if already tracked
            result = await session.execute(
                select(GovernanceActivity)
                .where(GovernanceActivity.tx_hash == tx_hash)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                return True  # Already tracked
            
            # Create new activity record
            activity = GovernanceActivity(
                wallet_address=address,
                chain_id=chain_id,
                protocol=protocol,
                activity_type=activity_type,
                proposal_id=proposal_id,
                tx_hash=tx_hash,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            session.add(activity)
            await session.commit()
            
            logger.info(f"Tracked {activity_type} for {address} on {protocol}")
            return True
        except Exception as e:
            logger.error(f"Error in _track_activity: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def get_governance_score(
        self,
        address: str,
        session=None
    ) -> int:
        """
        Calculate governance reputation score
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Governance score (0-100)
        """
        try:
            from database.connection import get_session
            from database.models import GovernanceActivity
            from sqlalchemy import select, func
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_governance_score(address, db_session)
            else:
                return await self._calculate_governance_score(address, session)
        except Exception as e:
            logger.error(f"Error calculating governance score: {e}", exc_info=True)
            return 0
    
    async def _calculate_governance_score(self, address: str, session) -> int:
        """Calculate governance score from activities"""
        from database.models import GovernanceActivity
        from sqlalchemy import select, func
        from collections import Counter
        
        try:
            # Get all governance activities
            result = await session.execute(
                select(GovernanceActivity)
                .where(GovernanceActivity.wallet_address == address)
            )
            activities = result.scalars().all()
            
            if not activities:
                return 0
            
            # Count activities by type
            activity_counts = Counter(activity.activity_type for activity in activities)
            
            # Calculate score
            score = 0
            score += activity_counts.get('vote', 0) * self.ACTIVITY_SCORES['vote']
            score += activity_counts.get('proposal', 0) * self.ACTIVITY_SCORES['proposal']
            score += activity_counts.get('delegation', 0) * self.ACTIVITY_SCORES['delegation']
            score += activity_counts.get('delegate', 0) * self.ACTIVITY_SCORES['delegate']
            
            # Cap at maximum
            return min(score, self.MAX_GOVERNANCE_SCORE)
        except Exception as e:
            logger.error(f"Error in _calculate_governance_score: {e}", exc_info=True)
            return 0
    
    async def get_governance_activity(
        self,
        address: str,
        limit: int = 100,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get governance activity for an address
        
        Args:
            address: Wallet address
            limit: Maximum number of activities to return
            session: Database session (optional)
            
        Returns:
            List of activity dictionaries
        """
        try:
            from database.connection import get_session
            from database.models import GovernanceActivity
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_activities(address, limit, db_session)
            else:
                return await self._get_activities(address, limit, session)
        except Exception as e:
            logger.error(f"Error getting governance activity: {e}", exc_info=True)
            return []
    
    async def _get_activities(self, address: str, limit: int, session) -> List[Dict[str, Any]]:
        """Get activities from database"""
        from database.models import GovernanceActivity
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(GovernanceActivity)
                .where(GovernanceActivity.wallet_address == address)
                .order_by(GovernanceActivity.timestamp.desc())
                .limit(limit)
            )
            activities = result.scalars().all()
            
            return [
                {
                    "id": activity.id,
                    "protocol": activity.protocol,
                    "activity_type": activity.activity_type,
                    "proposal_id": activity.proposal_id,
                    "tx_hash": activity.tx_hash,
                    "timestamp": activity.timestamp.isoformat() if activity.timestamp else None,
                    "metadata": activity.extra_metadata or {},
                }
                for activity in activities
            ]
        except Exception as e:
            logger.error(f"Error in _get_activities: {e}", exc_info=True)
            return []


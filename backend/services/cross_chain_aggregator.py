"""
Cross-chain score aggregator for unified credit identity
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from utils.logger import get_logger
from services.chain_registry import ChainRegistry

logger = get_logger(__name__)


class CrossChainAggregator:
    """Service for aggregating scores across multiple chains"""
    
    def __init__(self):
        self.chain_registry = ChainRegistry()
    
    async def get_unified_identity(
        self,
        address: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Get or create unified identity for an address
        
        Args:
            address: Primary wallet address
            session: Database session (optional)
            
        Returns:
            Unified identity dict with linked addresses
        """
        try:
            from database.connection import get_session
            from database.models import UnifiedIdentity
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_or_create_identity(address, db_session)
            else:
                return await self._get_or_create_identity(address, session)
        except Exception as e:
            logger.error(f"Error getting unified identity: {e}", exc_info=True)
            return None
    
    async def _get_or_create_identity(self, address: str, session) -> Optional[Dict[str, Any]]:
        """Get or create unified identity"""
        from database.models import UnifiedIdentity
        from sqlalchemy import select
        
        try:
            # Try to find existing unified identity
            result = await session.execute(
                select(UnifiedIdentity)
                .where(UnifiedIdentity.primary_address == address)
                .limit(1)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Get all linked addresses
                all_links = await session.execute(
                    select(UnifiedIdentity)
                    .where(UnifiedIdentity.primary_address == address)
                )
                linked_addresses = [
                    {
                        "chain_id": link.chain_id,
                        "address": link.address,
                        "linked_via": link.linked_via,
                        "verified": link.verified,
                    }
                    for link in all_links.scalars().all()
                ]
                
                return {
                    "id": existing.id,
                    "primary_address": existing.primary_address,
                    "linked_addresses": linked_addresses,
                }
            
            # Create new unified identity (same address on QIE)
            default_chain = self.chain_registry.get_default_chain()
            new_identity = UnifiedIdentity(
                primary_address=address,
                chain_id=default_chain.chain_id,
                address=address,
                linked_via='same_address',
                verified=False
            )
            session.add(new_identity)
            await session.commit()
            
            return {
                "id": new_identity.id,
                "primary_address": address,
                "linked_addresses": [{
                    "chain_id": default_chain.chain_id,
                    "address": address,
                    "linked_via": "same_address",
                    "verified": False,
                }],
            }
        except Exception as e:
            logger.error(f"Error in _get_or_create_identity: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def link_address(
        self,
        primary_address: str,
        address: str,
        chain_id: int,
        link_type: str = 'manual',
        bridge_tx_hash: Optional[str] = None,
        session=None
    ) -> bool:
        """
        Link an address to unified identity
        
        Args:
            primary_address: Primary wallet address
            address: Address to link
            chain_id: Chain ID of the address
            link_type: 'same_address', 'bridge', or 'manual'
            bridge_tx_hash: Bridge transaction hash (if linked via bridge)
            session: Database session (optional)
            
        Returns:
            True if linked successfully
        """
        try:
            from database.connection import get_session
            from database.models import UnifiedIdentity
            
            if session is None:
                async with get_session() as db_session:
                    return await self._link_address(
                        primary_address, address, chain_id, link_type, bridge_tx_hash, db_session
                    )
            else:
                return await self._link_address(
                    primary_address, address, chain_id, link_type, bridge_tx_hash, session
                )
        except Exception as e:
            logger.error(f"Error linking address: {e}", exc_info=True)
            return False
    
    async def _link_address(
        self,
        primary_address: str,
        address: str,
        chain_id: int,
        link_type: str,
        bridge_tx_hash: Optional[str],
        session
    ) -> bool:
        """Link address to identity"""
        from database.models import UnifiedIdentity
        from sqlalchemy import select
        
        try:
            # Check if already linked
            result = await session.execute(
                select(UnifiedIdentity)
                .where(
                    UnifiedIdentity.address == address,
                    UnifiedIdentity.chain_id == chain_id
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info(f"Address {address} on chain {chain_id} already linked")
                return True
            
            # Create new link
            new_link = UnifiedIdentity(
                primary_address=primary_address,
                chain_id=chain_id,
                address=address,
                linked_via=link_type,
                bridge_tx_hash=bridge_tx_hash,
                verified=(link_type == 'same_address')  # Auto-verify same address
            )
            session.add(new_link)
            await session.commit()
            
            logger.info(f"Linked address {address} on chain {chain_id} to {primary_address}")
            return True
        except Exception as e:
            logger.error(f"Error in _link_address: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def aggregate_scores(
        self,
        unified_identity_id: int,
        session=None
    ) -> Dict[str, Any]:
        """
        Aggregate scores across all linked chains
        
        Args:
            unified_identity_id: Unified identity ID
            session: Database session (optional)
            
        Returns:
            Aggregated score information
        """
        try:
            from database.connection import get_session
            from database.models import ChainScore, UnifiedIdentity
            from sqlalchemy import select, func
            
            if session is None:
                async with get_session() as db_session:
                    return await self._aggregate_scores(unified_identity_id, db_session)
            else:
                return await self._aggregate_scores(unified_identity_id, session)
        except Exception as e:
            logger.error(f"Error aggregating scores: {e}", exc_info=True)
            return {}
    
    async def _aggregate_scores(self, unified_identity_id: int, session) -> Dict[str, Any]:
        """Aggregate scores from all chains"""
        from database.models import ChainScore, UnifiedIdentity
        from sqlalchemy import select, func
        
        try:
            # Get all chain scores for this identity
            result = await session.execute(
                select(ChainScore)
                .where(ChainScore.unified_identity_id == unified_identity_id)
                .order_by(ChainScore.computed_at.desc())
            )
            chain_scores = result.scalars().all()
            
            if not chain_scores:
                return {
                    "unified_score": 0,
                    "chain_scores": [],
                    "weighted_average": 0,
                }
            
            # Calculate weighted average
            weighted_score = self.calculate_unified_score(chain_scores)
            
            # Get chain details
            chain_details = []
            for cs in chain_scores:
                chain_info = self.chain_registry.get_chain_info(cs.chain_id)
                chain_details.append({
                    "chain_id": cs.chain_id,
                    "chain_name": chain_info.name if chain_info else f"Chain {cs.chain_id}",
                    "wallet_address": cs.wallet_address,
                    "score": cs.score,
                    "risk_band": cs.risk_band,
                    "computed_at": cs.computed_at.isoformat() if cs.computed_at else None,
                })
            
            return {
                "unified_score": int(weighted_score),
                "chain_scores": chain_details,
                "weighted_average": int(weighted_score),
                "chain_count": len(chain_scores),
            }
        except Exception as e:
            logger.error(f"Error in _aggregate_scores: {e}", exc_info=True)
            return {}
    
    def calculate_unified_score(self, chain_scores: List) -> float:
        """
        Calculate unified score using weighted aggregation
        
        Args:
            chain_scores: List of ChainScore objects
            
        Returns:
            Weighted average score
        """
        if not chain_scores:
            return 0.0
        
        # Simple average for now (can be enhanced with activity-based weighting)
        total_score = sum(cs.score for cs in chain_scores)
        return total_score / len(chain_scores)
        
        # Future enhancement: Weight by activity/volume
        # weights = [self._calculate_chain_weight(cs) for cs in chain_scores]
        # weighted_sum = sum(cs.score * w for cs, w in zip(chain_scores, weights))
        # total_weight = sum(weights)
        # return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_chain_weight(self, chain_score) -> float:
        """Calculate weight for a chain based on activity"""
        # Placeholder - would calculate based on transaction volume, activity, etc.
        return 1.0


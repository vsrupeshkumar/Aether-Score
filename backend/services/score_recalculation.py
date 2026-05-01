"""
Score Recalculation Service

Periodically recalculates scores for active users based on new transactions.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database.models import Score, Transaction, User
from database.connection import get_db_session
from database.repositories import ScoreRepository
from services.ml_scoring import MLScoringService
from services.transaction_indexer import TransactionIndexer
from utils.logger import get_logger
from rq import Queue
from redis import Redis

logger = get_logger(__name__)

# Redis connection for async processing
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
recalculation_queue = Queue("recalculation", connection=redis_conn)


class ScoreRecalculationService:
    """Service for recalculating credit scores"""
    
    def __init__(self):
        self.ml_scoring = MLScoringService()
        self.indexer = TransactionIndexer()
        self.recalculation_threshold = float(os.getenv("RECALCULATION_THRESHOLD", "0.05"))  # 5% change threshold
        self.max_batch_size = int(os.getenv("RECALCULATION_BATCH_SIZE", "100"))
    
    async def recalculate_score(
        self,
        address: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Recalculate score for an address
        
        Args:
            address: Wallet address
            force: Force recalculation even if recent
            
        Returns:
            Recalculation result
        """
        try:
            # Check if recalculation is needed
            if not force:
                should_recalculate = await self._should_recalculate(address)
                if not should_recalculate:
                    return {
                        "status": "skipped",
                        "message": "Score is up to date",
                    }
            
            # Index new transactions first
            await self.indexer.index_address_transactions(address)
            
            # Recalculate score
            score_result = await self.ml_scoring.compute_score(address)
            new_score = score_result.get("score", 500)
            new_risk_band = score_result.get("riskBand", 2)
            
            # Get current score
            async with get_db_session() as session:
                current_score_data = await ScoreRepository.get_score(session, address)
                current_score = current_score_data.score if current_score_data else None
                
                # Check if change is significant
                if current_score:
                    score_change = abs(new_score - current_score) / current_score
                    
                    if score_change < self.recalculation_threshold and not force:
                        return {
                            "status": "skipped",
                            "message": f"Score change ({score_change:.2%}) below threshold",
                            "current_score": current_score,
                            "new_score": new_score,
                        }
                
                # Update score
                from services.blockchain import BlockchainService
                blockchain_service = BlockchainService()
                
                tx_hash = await blockchain_service.update_score(
                    address,
                    new_score,
                    new_risk_band
                )
                
                logger.info(
                    f"Score recalculated for {address}",
                    extra={
                        "address": address,
                        "old_score": current_score,
                        "new_score": new_score,
                        "tx_hash": tx_hash,
                    }
                )
                
                return {
                    "status": "success",
                    "address": address,
                    "old_score": current_score,
                    "new_score": new_score,
                    "risk_band": new_risk_band,
                    "tx_hash": tx_hash,
                }
                
        except Exception as e:
            logger.error(f"Error recalculating score: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def _should_recalculate(self, address: str) -> bool:
        """Check if score should be recalculated"""
        try:
            async with get_db_session() as session:
                score_data = await ScoreRepository.get_score(session, address)
                
                if not score_data:
                    return True  # No score exists, calculate it
                
                # Check if there are new transactions since last update
                last_updated = score_data.last_updated or score_data.computed_at
                
                if not last_updated:
                    return True
                
                # Check for new transactions
                stmt = select(Transaction).where(
                    and_(
                        Transaction.wallet_address == address,
                        Transaction.block_timestamp > last_updated
                    )
                ).limit(1)
                
                result = await session.execute(stmt)
                has_new_txs = result.scalar_one_or_none() is not None
                
                # Also check if score is old (more than 7 days)
                days_since_update = (datetime.now() - last_updated).days
                is_old = days_since_update > 7
                
                return has_new_txs or is_old
                
        except Exception as e:
            logger.warning(f"Error checking recalculation need: {e}")
            return True  # Default to recalculating on error
    
    async def batch_recalculate(
        self,
        addresses: Optional[List[str]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Recalculate scores for multiple addresses
        
        Args:
            addresses: List of addresses (None = all active users)
            priority: Priority level (high, normal, low)
            
        Returns:
            Batch recalculation result
        """
        try:
            if addresses is None:
                # Get all active users
                async with get_db_session() as session:
                    stmt = select(User).where(User.deleted_at.is_(None))
                    result = await session.execute(stmt)
                    users = result.scalars().all()
                    addresses = [user.wallet_address for user in users]
            
            # Process in batches
            results = {
                "total": len(addresses),
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "results": [],
            }
            
            for i in range(0, len(addresses), self.max_batch_size):
                batch = addresses[i:i + self.max_batch_size]
                
                for address in batch:
                    result = await self.recalculate_score(address)
                    
                    if result.get("status") == "success":
                        results["successful"] += 1
                    elif result.get("status") == "skipped":
                        results["skipped"] += 1
                    else:
                        results["failed"] += 1
                    
                    results["results"].append(result)
            
            logger.info(
                f"Batch recalculation completed",
                extra={
                    "total": results["total"],
                    "successful": results["successful"],
                    "failed": results["failed"],
                    "skipped": results["skipped"],
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch recalculation: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }
    
    def enqueue_recalculation(self, address: str, priority: str = "normal") -> str:
        """
        Enqueue score recalculation for async processing
        
        Returns:
            Job ID
        """
        from services.tasks.recalculation_worker import recalculate_score_task
        
        job = recalculation_queue.enqueue(
            recalculate_score_task,
            address,
            job_timeout="5m",
            job_id=f"recalc_{address}_{datetime.now().timestamp()}"
        )
        
        logger.info(f"Enqueued recalculation for {address}", extra={"job_id": job.id})
        return job.id


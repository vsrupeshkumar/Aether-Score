"""
Batch processing service for multiple addresses
"""
import os
import uuid
from typing import List, Dict, Any
from datetime import datetime
from database.connection import get_db_session
from database.repositories import BatchUpdateRepository, ScoreRepository
from services.scoring import ScoringService
from services.blockchain import BlockchainService
from utils.cache import cache_score, get_cached_score
from utils.logger import get_logger
from utils.metrics import record_score_computation

logger = get_logger(__name__)


class BatchService:
    """Service for batch processing operations"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.blockchain_service = BlockchainService()
        self.batch_size = int(os.getenv("BATCH_SIZE", "10"))
    
    async def batch_compute_scores(self, addresses: List[str]) -> Dict[str, Dict]:
        """
        Compute scores for multiple addresses in batch
        
        Args:
            addresses: List of wallet addresses
            
        Returns:
            Dictionary mapping addresses to score results
        """
        results = {}
        
        # Check cache first
        for address in addresses:
            cached = get_cached_score(address)
            if cached:
                results[address] = cached
        
        # Compute scores for uncached addresses
        uncached = [addr for addr in addresses if addr not in results]
        
        if uncached:
            # Process in batches
            for i in range(0, len(uncached), self.batch_size):
                batch = uncached[i:i + self.batch_size]
                
                for address in batch:
                    try:
                        score_result = await self.scoring_service.compute_score(address)
                        results[address] = score_result
                        cache_score(address, score_result)
                    except Exception as e:
                        logger.error(f"Error computing score for {address}: {e}", exc_info=True)
                        results[address] = {"error": str(e)}
        
        # Store in database if configured
        if os.getenv("DATABASE_URL"):
            await self._store_batch_scores(results)
        
        return results
    
    async def batch_update_scores_on_chain(
        self,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Batch update scores on blockchain
        
        Args:
            updates: List of dicts with 'address', 'score', 'risk_band'
            
        Returns:
            Dictionary mapping addresses to transaction hashes
        """
        results = {}
        
        # Process in batches
        for i in range(0, len(updates), self.batch_size):
            batch = updates[i:i + self.batch_size]
            
            for update in batch:
                address = update["address"]
                score = update["score"]
                risk_band = update["risk_band"]
                
                try:
                    tx_hash = await self.blockchain_service.update_score(
                        address,
                        score,
                        risk_band
                    )
                    results[address] = tx_hash
                except Exception as e:
                    logger.error(f"Error updating {address}: {e}", exc_info=True)
                    results[address] = f"error: {str(e)}"
        
        return results
    
    async def batch_get_scores_from_blockchain(
        self,
        addresses: List[str]
    ) -> Dict[str, Dict]:
        """
        Batch get scores from blockchain
        
        Args:
            addresses: List of wallet addresses
            
        Returns:
            Dictionary mapping addresses to score data
        """
        results = {}
        
        # Use batch RPC if available
        try:
            from utils.batch_rpc import batch_get_scores
            from database.connection import get_engine
            
            engine = get_engine()
            if engine:
                contract_abi = self.blockchain_service.contract_abi
                batch_results = batch_get_scores(addresses, contract_abi)
                
                for address, result in zip(addresses, batch_results):
                    if result:
                        results[address] = {
                            "score": result[0] if isinstance(result, (list, tuple)) else result.get("score", 0),
                            "riskBand": result[1] if isinstance(result, (list, tuple)) else result.get("riskBand", 0),
                            "lastUpdated": result[2] if isinstance(result, (list, tuple)) else result.get("lastUpdated", None)
                        }
        except Exception as e:
            logger.warning(f"Batch RPC failed, using individual calls: {e}")
            
            # Fallback to individual calls
            for address in addresses:
                try:
                    score_data = await self.blockchain_service.get_score(address)
                    if score_data:
                        results[address] = score_data
                except Exception as e:
                    logger.error(f"Error getting score for {address}: {e}", exc_info=True)
        
        return results
    
    async def batch_warm_cache(self, addresses: List[str]) -> int:
        """
        Warm cache by preloading scores for addresses
        
        Args:
            addresses: List of wallet addresses
            
        Returns:
            Number of addresses cached
        """
        count = 0
        
        for address in addresses:
            try:
                # Compute and cache score
                score_result = await self.scoring_service.compute_score(address)
                cache_score(address, score_result)
                count += 1
            except Exception as e:
                logger.warning(f"Error warming cache for {address}: {e}", extra={"error": str(e)})
        
        return count
    
    async def _store_batch_scores(self, scores: Dict[str, Dict]):
        """Store batch scores in database"""
        if not os.getenv("DATABASE_URL"):
            return
        
        try:
            async with get_db_session() as session:
                for address, score_data in scores.items():
                    if "error" not in score_data:
                        await ScoreRepository.upsert_score(
                            session,
                            address,
                            score_data["score"],
                            score_data["riskBand"],
                        )
        except Exception as e:
            logger.error(f"Error storing batch scores: {e}", exc_info=True)


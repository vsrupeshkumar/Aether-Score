"""
Background tasks for score computation
"""
import os
import asyncio
from typing import Dict, List
from services.scoring import ScoringService
from database.connection import get_db_session
from database.repositories import ScoreRepository, ScoreHistoryRepository
from utils.cache import cache_score, invalidate_score_cache
from utils.logger import get_logger

logger = get_logger(__name__)


def compute_score_task(wallet_address: str) -> Dict:
    """
    Compute score in background (synchronous wrapper for async function)
    
    Args:
        wallet_address: Wallet address to compute score for
        
    Returns:
        Score computation result
    """
    try:
        scoring_service = ScoringService()
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(scoring_service.compute_score(wallet_address))
            
            # Store in database if configured
            if os.getenv("DATABASE_URL"):
                loop.run_until_complete(_store_score_in_db(wallet_address, result))
            
            # Cache result
            cache_score(wallet_address, result)
            
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Score computation task failed: {e}", exc_info=True, extra={"address": wallet_address})
        raise


async def _store_score_in_db(wallet_address: str, score_data: Dict):
    """Store score in database"""
    try:
        async with get_db_session() as session:
            # Upsert score
            await ScoreRepository.upsert_score(
                session,
                wallet_address,
                score_data["score"],
                score_data["riskBand"],
            )
            
            # Add to history
            await ScoreHistoryRepository.add_history(
                session,
                wallet_address,
                score_data["score"],
                score_data["riskBand"],
            )
    except Exception as e:
        logger.error(f"Error storing score in DB: {e}", exc_info=True, extra={"address": wallet_address})


def compute_scores_batch(wallet_addresses: List[str]) -> Dict[str, Dict]:
    """
    Compute scores for multiple addresses in batch
    
    Args:
        wallet_addresses: List of wallet addresses
        
    Returns:
        Dictionary mapping addresses to score results
    """
    results = {}
    scoring_service = ScoringService()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        for address in wallet_addresses:
            try:
                result = loop.run_until_complete(scoring_service.compute_score(address))
                results[address] = result
                
                # Store in database if configured
                if os.getenv("DATABASE_URL"):
                    loop.run_until_complete(_store_score_in_db(address, result))
                
                # Cache result
                cache_score(address, result)
            except Exception as e:
                logger.error(f"Error computing score for {address}: {e}", exc_info=True)
                results[address] = {"error": str(e)}
    finally:
        loop.close()
    
    return results


def recalculate_stale_scores(hours: int = 24) -> int:
    """
    Recalculate scores that haven't been updated in specified hours
    
    Args:
        hours: Number of hours to consider stale
        
    Returns:
        Number of scores recalculated
    """
    if not os.getenv("DATABASE_URL"):
        return 0
    
    try:
        from datetime import datetime, timedelta
        from database.connection import get_db_session
        from database.repositories import ScoreRepository
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async with get_db_session() as session:
                stale_scores = await ScoreRepository.get_recent_scores(session, limit=1000, hours=hours)
                
                count = 0
                for score in stale_scores:
                    if score.last_updated < cutoff:
                        try:
                            compute_score_task(score.wallet_address)
                            count += 1
                        except Exception as e:
                            logger.error(f"Error recalculating score: {e}", exc_info=True)
        finally:
            loop.close()
        
        return count
    except Exception as e:
        logger.error(f"Error in recalculate_stale_scores: {e}", exc_info=True)
        return 0


"""
Background tasks for blockchain operations
"""
import os
import asyncio
from typing import List, Dict
from services.blockchain import BlockchainService
from database.connection import get_db_session
from database.repositories import ScoreRepository, ScoreHistoryRepository
from utils.cache import invalidate_score_cache, invalidate_pattern
from utils.logger import get_logger

logger = get_logger(__name__)


def update_score_on_chain_task(wallet_address: str, score: int, risk_band: int) -> str:
    """
    Update score on blockchain in background
    
    Args:
        wallet_address: Wallet address
        score: Credit score
        risk_band: Risk band
        
    Returns:
        Transaction hash
    """
    try:
        blockchain_service = BlockchainService()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tx_hash = loop.run_until_complete(
                blockchain_service.update_score(wallet_address, score, risk_band)
            )
            
            # Invalidate caches
            invalidate_score_cache(wallet_address)
            invalidate_pattern(f"rpc:getScore:*{wallet_address}*")
            
            return tx_hash
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Blockchain update task failed: {e}", exc_info=True, extra={"address": wallet_address})
        raise


def batch_update_scores_task(updates: List[Dict[str, any]]) -> Dict[str, str]:
    """
    Batch update multiple scores on blockchain
    
    Args:
        updates: List of dicts with 'address', 'score', 'risk_band'
        
    Returns:
        Dictionary mapping addresses to transaction hashes
    """
    results = {}
    blockchain_service = BlockchainService()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        for update in updates:
            address = update["address"]
            score = update["score"]
            risk_band = update["risk_band"]
            
            try:
                tx_hash = loop.run_until_complete(
                    blockchain_service.update_score(address, score, risk_band)
                )
                results[address] = tx_hash
                
                # Invalidate caches
                invalidate_score_cache(address)
                invalidate_pattern(f"rpc:getScore:*{address}*")
            except Exception as e:
                logger.error(f"Error updating {address}: {e}", exc_info=True)
                results[address] = f"error: {str(e)}"
    finally:
        loop.close()
    
    return results


async def sync_scores_from_blockchain(addresses: List[str]) -> Dict[str, Dict]:
    """
    Sync scores from blockchain to database
    
    Args:
        addresses: List of wallet addresses
        
    Returns:
        Dictionary mapping addresses to score data
    """
    if not os.getenv("DATABASE_URL"):
        return {}
    
    try:
        blockchain_service = BlockchainService()
        results = {}
        
        async with get_db_session() as session:
            for address in addresses:
                try:
                    # Get from blockchain
                    score_data = await blockchain_service.get_score(address)
                    
                    if score_data and score_data.get("score", 0) > 0:
                        # Store in database
                        await ScoreRepository.upsert_score(
                            session,
                            address,
                            score_data["score"],
                            score_data["riskBand"],
                        )
                        
                        results[address] = score_data
                except Exception as e:
                    logger.error(f"Error syncing {address}: {e}", exc_info=True)
                    results[address] = {"error": str(e)}
        
        return results
    except Exception as e:
        logger.error(f"Error in sync_scores_from_blockchain: {e}", exc_info=True)
        return {}


"""
Background worker for transaction indexing
Uses RQ (Redis Queue) for async processing
"""

import os
from rq import Queue
from redis import Redis
from typing import Dict, Any
from services.transaction_indexer import TransactionIndexer
from utils.logger import get_logger

logger = get_logger(__name__)

# Redis connection
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
indexer_queue = Queue("indexer", connection=redis_conn)


def index_address_task(address: str, from_block: int = None, to_block: int = None, force_reindex: bool = False) -> Dict[str, Any]:
    """
    RQ task for indexing transactions
    
    Args:
        address: Wallet address to index
        from_block: Starting block number
        to_block: Ending block number
        force_reindex: Force reindexing even if already indexed
        
    Returns:
        Dict with indexing results
    """
    try:
        indexer = TransactionIndexer()
        # Note: This is a sync wrapper - in production, use async_to_sync or make indexer sync
        import asyncio
        result = asyncio.run(
            indexer.index_address_transactions(address, from_block, to_block, force_reindex)
        )
        return result
    except Exception as e:
        logger.error(f"Error in index_address_task: {e}", exc_info=True)
        raise


def enqueue_indexing(address: str, from_block: int = None, to_block: int = None, force_reindex: bool = False) -> str:
    """
    Enqueue an address for indexing
    
    Returns:
        Job ID
    """
    job = indexer_queue.enqueue(
        index_address_task,
        address,
        from_block,
        to_block,
        force_reindex,
        job_timeout="10m"  # 10 minute timeout
    )
    logger.info(f"Enqueued indexing job for {address}", extra={"job_id": job.id})
    return job.id


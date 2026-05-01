"""
RQ Worker for blockchain update tasks
"""
import os
from rq import Worker, Queue, Connection
from redis import Redis
from utils.logger import get_logger

logger = get_logger(__name__)


def start_blockchain_worker():
    """Start RQ worker for blockchain update tasks"""
    redis_url = os.getenv("RQ_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/2")
    
    try:
        redis_conn = Redis.from_url(redis_url)
        
        # Create queue
        blockchain_queue = Queue("blockchain_updates", connection=redis_conn)
        
        # Start worker
        with Connection(redis_conn):
            worker = Worker([blockchain_queue], name="blockchain_worker")
            logger.info("Starting blockchain update worker")
            worker.work()
    except Exception as e:
        logger.error(f"Error starting blockchain worker: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    start_blockchain_worker()


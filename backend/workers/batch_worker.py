"""
RQ Worker for batch processing tasks
"""
import os
from rq import Worker, Queue, Connection
from redis import Redis
from utils.logger import get_logger

logger = get_logger(__name__)


def start_batch_worker():
    """Start RQ worker for batch processing tasks"""
    redis_url = os.getenv("RQ_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/2")
    
    try:
        redis_conn = Redis.from_url(redis_url)
        
        # Create queue
        batch_queue = Queue("batch_processing", connection=redis_conn)
        
        # Start worker
        with Connection(redis_conn):
            worker = Worker([batch_queue], name="batch_worker")
            logger.info("Starting batch processing worker")
            worker.work()
    except Exception as e:
        logger.error(f"Error starting batch worker: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    start_batch_worker()


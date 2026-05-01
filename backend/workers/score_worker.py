"""
RQ Worker for score computation tasks
"""
import os
from rq import Worker, Queue, Connection
from redis import Redis
from utils.logger import get_logger

logger = get_logger(__name__)


def start_score_worker():
    """Start RQ worker for score computation tasks"""
    redis_url = os.getenv("RQ_REDIS_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/2")
    
    try:
        redis_conn = Redis.from_url(redis_url)
        
        # Create queue
        score_queue = Queue("score_computation", connection=redis_conn)
        
        # Start worker
        with Connection(redis_conn):
            worker = Worker([score_queue], name="score_worker")
            logger.info("Starting score computation worker")
            worker.work()
    except Exception as e:
        logger.error(f"Error starting score worker: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    start_score_worker()


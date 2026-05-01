"""
Background job for token distribution when threshold reached
"""
import asyncio
from utils.logger import get_logger
from services.token_distributor import TokenDistributorService

logger = get_logger(__name__)


async def check_and_distribute_tokens():
    """Check threshold and distribute tokens if reached"""
    try:
        service = TokenDistributorService()
        
        # Check threshold
        threshold_check = await service.check_distribution_threshold()
        
        if threshold_check.get("threshold_reached", False):
            logger.info(f"Threshold reached ({threshold_check.get('total_pending', 0)} NCRD), executing distribution...")
            
            # Execute distribution
            result = await service.execute_onchain_distribution()
            
            if result.get("success"):
                logger.info(f"Successfully distributed {result.get('distributed_count', 0)} rewards")
            else:
                logger.error(f"Failed to distribute tokens: {result.get('error')}")
        else:
            logger.debug(f"Threshold not reached ({threshold_check.get('total_pending', 0)}/{threshold_check.get('threshold', 100)} NCRD)")
    except Exception as e:
        logger.error(f"Error checking and distributing tokens: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(check_and_distribute_tokens())


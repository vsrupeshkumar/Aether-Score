"""
Recalculation Worker Tasks

RQ tasks for async score recalculation.
"""

import asyncio
from services.score_recalculation import ScoreRecalculationService
from utils.logger import get_logger

logger = get_logger(__name__)


def recalculate_score_task(address: str) -> dict:
    """
    RQ task for recalculating a score
    
    Args:
        address: Wallet address
        
    Returns:
        Recalculation result
    """
    try:
        service = ScoreRecalculationService()
        result = asyncio.run(service.recalculate_score(address))
        return result
    except Exception as e:
        logger.error(f"Error in recalculation task: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
        }


"""
Background job for updating leaderboard rankings
"""
import asyncio
from utils.logger import get_logger
from services.leaderboard import LeaderboardService

logger = get_logger(__name__)


async def update_leaderboards():
    """Update all leaderboard categories"""
    try:
        service = LeaderboardService()
        
        categories = ['all_time', 'monthly', 'weekly']
        
        for category in categories:
            logger.info(f"Updating {category} leaderboard...")
            success = await service.update_leaderboard(category)
            if success:
                logger.info(f"Successfully updated {category} leaderboard")
            else:
                logger.error(f"Failed to update {category} leaderboard")
    except Exception as e:
        logger.error(f"Error updating leaderboards: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(update_leaderboards())


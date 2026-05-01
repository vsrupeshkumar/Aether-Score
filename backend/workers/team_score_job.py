"""
Background job for updating team scores
"""
import asyncio
from utils.logger import get_logger
from services.team_score import TeamScoreService
from database.connection import get_session
from database.models import Team
from sqlalchemy import select

logger = get_logger(__name__)


async def update_team_scores():
    """Recalculate all team scores"""
    try:
        service = TeamScoreService()
        
        async with get_session() as session:
            # Get all teams
            result = await session.execute(select(Team))
            teams = result.scalars().all()
            
            logger.info(f"Updating scores for {len(teams)} teams...")
            
            for team in teams:
                try:
                    logger.info(f"Calculating score for team {team.id} ({team.team_name})...")
                    score_result = await service.calculate_team_score(team.id, session)
                    
                    if score_result:
                        logger.info(f"Team {team.id} score: {score_result.get('aggregate_score', 0)}")
                    else:
                        logger.warning(f"Failed to calculate score for team {team.id}")
                except Exception as e:
                    logger.error(f"Error calculating score for team {team.id}: {e}", exc_info=True)
            
            await session.commit()
            
        logger.info("Finished updating team scores")
    except Exception as e:
        logger.error(f"Error updating team scores: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(update_team_scores())


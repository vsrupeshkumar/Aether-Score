"""
Leaderboard service for ranking and leaderboard management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from utils.logger import get_logger
from services.scoring import ScoringService
from database.repositories import ScoreRepository

logger = get_logger(__name__)


class LeaderboardService:
    """Service for managing leaderboards and rankings"""
    
    # Leaderboard categories
    CATEGORIES = ['all_time', 'monthly', 'weekly']
    
    def __init__(self):
        self.scoring_service = ScoringService()
    
    async def get_top_scores(
        self,
        limit: int = 100,
        timeframe: Optional[str] = None,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get top N scores
        
        Args:
            limit: Number of top scores to return
            timeframe: Optional timeframe ('all_time', 'monthly', 'weekly')
            session: Database session (optional)
            
        Returns:
            List of top score dicts
        """
        try:
            from database.connection import get_session
            from database.models import LeaderboardEntry
            from sqlalchemy import select, desc
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_top_scores(limit, timeframe, db_session)
            else:
                return await self._get_top_scores(limit, timeframe, session)
        except Exception as e:
            logger.error(f"Error getting top scores: {e}", exc_info=True)
            return []
    
    async def _get_top_scores(
        self,
        limit: int,
        timeframe: Optional[str],
        session
    ) -> List[Dict[str, Any]]:
        """Get top scores from database"""
        from database.models import LeaderboardEntry
        from sqlalchemy import select, desc
        
        try:
            category = timeframe or 'all_time'
            
            query = select(LeaderboardEntry).where(
                LeaderboardEntry.category == category
            ).order_by(desc(LeaderboardEntry.score)).limit(limit)
            
            result = await session.execute(query)
            entries = result.scalars().all()
            
            return [
                {
                    "rank": entry.rank,
                    "wallet_address": entry.wallet_address,
                    "score": entry.score,
                    "risk_band": entry.risk_band,
                    "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
                }
                for entry in entries
            ]
        except Exception as e:
            logger.error(f"Error in _get_top_scores: {e}", exc_info=True)
            return []
    
    async def get_user_rank(
        self,
        address: str,
        category: str = 'all_time',
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's rank
        
        Args:
            address: Wallet address
            category: Leaderboard category
            session: Database session (optional)
            
        Returns:
            User rank dict or None if not found
        """
        try:
            from database.connection import get_session
            from database.models import LeaderboardEntry
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_user_rank(address, category, db_session)
            else:
                return await self._get_user_rank(address, category, session)
        except Exception as e:
            logger.error(f"Error getting user rank: {e}", exc_info=True)
            return None
    
    async def _get_user_rank(
        self,
        address: str,
        category: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Get user rank from database"""
        from database.models import LeaderboardEntry
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(LeaderboardEntry).where(
                    LeaderboardEntry.wallet_address == address,
                    LeaderboardEntry.category == category
                )
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                return None
            
            return {
                "rank": entry.rank,
                "wallet_address": address,
                "score": entry.score,
                "risk_band": entry.risk_band,
                "category": category,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _get_user_rank: {e}", exc_info=True)
            return None
    
    async def get_leaderboard_category(
        self,
        category: str,
        limit: int = 100,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard by category
        
        Args:
            category: Category ('all_time', 'monthly', 'weekly')
            limit: Number of entries to return
            session: Database session (optional)
            
        Returns:
            List of leaderboard entries
        """
        try:
            if category not in self.CATEGORIES:
                category = 'all_time'
            
            return await self.get_top_scores(limit, category, session)
        except Exception as e:
            logger.error(f"Error getting leaderboard category: {e}", exc_info=True)
            return []
    
    async def update_leaderboard(
        self,
        category: str = 'all_time',
        session=None
    ) -> bool:
        """
        Update leaderboard cache
        
        Args:
            category: Category to update
            session: Database session (optional)
            
        Returns:
            True if updated successfully
        """
        try:
            from database.connection import get_session
            from database.models import LeaderboardEntry, Score
            from sqlalchemy import select, desc, func
            from datetime import datetime, timedelta
            
            if session is None:
                async with get_session() as db_session:
                    return await self._update_leaderboard(category, db_session)
            else:
                return await self._update_leaderboard(category, session)
        except Exception as e:
            logger.error(f"Error updating leaderboard: {e}", exc_info=True)
            return False
    
    async def _update_leaderboard(
        self,
        category: str,
        session
    ) -> bool:
        """Update leaderboard in database"""
        from database.models import LeaderboardEntry, Score
        from sqlalchemy import select, desc, func, delete
        from datetime import datetime, timedelta
        
        try:
            # Calculate period dates
            now = datetime.utcnow()
            period_start = None
            period_end = None
            
            if category == 'monthly':
                period_start = datetime(now.year, now.month, 1)
                period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif category == 'weekly':
                period_start = now - timedelta(days=now.weekday())
                period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(days=7)
            
            # Delete existing entries for this category
            await session.execute(
                delete(LeaderboardEntry).where(LeaderboardEntry.category == category)
            )
            
            # Get all scores, ordered by score descending
            result = await session.execute(
                select(Score).order_by(desc(Score.score))
            )
            scores = result.scalars().all()
            
            # Create leaderboard entries
            rank = 1
            for score_obj in scores:
                entry = LeaderboardEntry(
                    wallet_address=score_obj.wallet_address,
                    score=score_obj.score,
                    risk_band=score_obj.riskBand,
                    rank=rank,
                    category=category,
                    period_start=period_start,
                    period_end=period_end,
                )
                session.add(entry)
                rank += 1
            
            await session.commit()
            
            logger.info(f"Updated {category} leaderboard with {rank - 1} entries")
            return True
        except Exception as e:
            logger.error(f"Error in _update_leaderboard: {e}", exc_info=True)
            await session.rollback()
            return False


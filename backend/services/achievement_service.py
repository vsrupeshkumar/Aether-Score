"""
Achievement service for unlocking and managing user badges
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import get_logger
from database.connection import get_session
from database.models import Achievement, UserAchievement
from sqlalchemy import select, and_

logger = get_logger(__name__)


class AchievementService:
    """Service for managing achievements and badges"""
    
    # Achievement definitions
    ACHIEVEMENTS = {
        "first_score": {
            "id": "first_score",
            "name": "First Steps",
            "description": "Generate your first credit score",
            "icon": "🎯",
            "category": "milestone",
        },
        "score_100": {
            "id": "score_100",
            "name": "Getting Started",
            "description": "Reach a score of 100",
            "icon": "⭐",
            "category": "score",
            "threshold": 100,
        },
        "score_200": {
            "id": "score_200",
            "name": "Rising Star",
            "description": "Reach a score of 200",
            "icon": "🌟",
            "category": "score",
            "threshold": 200,
        },
        "score_500": {
            "id": "score_500",
            "name": "Halfway There",
            "description": "Reach a score of 500",
            "icon": "💫",
            "category": "score",
            "threshold": 500,
        },
        "score_750": {
            "id": "score_750",
            "name": "Excellent Credit",
            "description": "Reach a score of 750",
            "icon": "🏆",
            "category": "score",
            "threshold": 750,
        },
        "score_1000": {
            "id": "score_1000",
            "name": "Perfect Score",
            "description": "Reach the maximum score of 1000",
            "icon": "👑",
            "category": "score",
            "threshold": 1000,
        },
        "first_loan": {
            "id": "first_loan",
            "name": "First Loan",
            "description": "Take out your first loan",
            "icon": "💰",
            "category": "loan",
        },
        "loan_master": {
            "id": "loan_master",
            "name": "Loan Master",
            "description": "Repay 10 loans successfully",
            "icon": "🎖️",
            "category": "loan",
            "threshold": 10,
        },
        "staking_bronze": {
            "id": "staking_bronze",
            "name": "Bronze Staker",
            "description": "Reach Bronze staking tier",
            "icon": "🥉",
            "category": "staking",
        },
        "staking_silver": {
            "id": "staking_silver",
            "name": "Silver Staker",
            "description": "Reach Silver staking tier",
            "icon": "🥈",
            "category": "staking",
        },
        "staking_gold": {
            "id": "staking_gold",
            "name": "Gold Staker",
            "description": "Reach Gold staking tier",
            "icon": "🥇",
            "category": "staking",
        },
        "tx_10": {
            "id": "tx_10",
            "name": "Active User",
            "description": "Complete 10 transactions",
            "icon": "📊",
            "category": "transaction",
            "threshold": 10,
        },
        "tx_50": {
            "id": "tx_50",
            "name": "Power User",
            "description": "Complete 50 transactions",
            "icon": "📈",
            "category": "transaction",
            "threshold": 50,
        },
        "tx_100": {
            "id": "tx_100",
            "name": "Super User",
            "description": "Complete 100 transactions",
            "icon": "🔥",
            "category": "transaction",
            "threshold": 100,
        },
        "tx_500": {
            "id": "tx_500",
            "name": "Transaction Master",
            "description": "Complete 500 transactions",
            "icon": "💎",
            "category": "transaction",
            "threshold": 500,
        },
    }
    
    def __init__(self):
        pass
    
    async def check_achievements(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Check and unlock achievements for user
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of newly unlocked achievements
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._check_achievements(address, db_session)
            else:
                return await self._check_achievements(address, session)
        except Exception as e:
            logger.error(f"Error checking achievements: {e}", exc_info=True)
            return []
    
    async def _check_achievements(
        self,
        address: str,
        session
    ) -> List[Dict[str, Any]]:
        """Check achievements and unlock new ones"""
        try:
            # Get user's current stats
            stats = await self._get_user_stats(address, session)
            
            # Get already unlocked achievements
            result = await session.execute(
                select(UserAchievement).where(UserAchievement.wallet_address == address)
            )
            unlocked = {ua.achievement_id for ua in result.scalars().all()}
            
            newly_unlocked = []
            
            # Check each achievement
            for achievement_id, achievement_def in self.ACHIEVEMENTS.items():
                if achievement_id in unlocked:
                    continue
                
                if await self._check_achievement_condition(
                    achievement_id, achievement_def, stats, session
                ):
                    # Unlock achievement
                    achievement = await self._unlock_achievement(
                        address, achievement_id, session
                    )
                    if achievement:
                        newly_unlocked.append(achievement)
            
            return newly_unlocked
        except Exception as e:
            logger.error(f"Error in _check_achievements: {e}", exc_info=True)
            return []
    
    async def _check_achievement_condition(
        self,
        achievement_id: str,
        achievement_def: Dict[str, Any],
        stats: Dict[str, Any],
        session
    ) -> bool:
        """Check if achievement condition is met"""
        category = achievement_def.get("category")
        
        if achievement_id == "first_score":
            return stats.get("has_score", False)
        
        if category == "score":
            threshold = achievement_def.get("threshold", 0)
            return stats.get("current_score", 0) >= threshold
        
        if category == "loan":
            if achievement_id == "first_loan":
                return stats.get("total_loans", 0) > 0
            elif achievement_id == "loan_master":
                threshold = achievement_def.get("threshold", 10)
                return stats.get("repaid_loans", 0) >= threshold
        
        if category == "staking":
            staking_tier = stats.get("staking_tier", 0)
            if achievement_id == "staking_bronze":
                return staking_tier >= 1
            elif achievement_id == "staking_silver":
                return staking_tier >= 2
            elif achievement_id == "staking_gold":
                return staking_tier >= 3
        
        if category == "transaction":
            threshold = achievement_def.get("threshold", 0)
            return stats.get("total_transactions", 0) >= threshold
        
        return False
    
    async def _get_user_stats(
        self,
        address: str,
        session
    ) -> Dict[str, Any]:
        """Get user statistics for achievement checking"""
        try:
            from database.models import Score, Loan, Transaction
            from services.staking import StakingService
            
            stats = {
                "has_score": False,
                "current_score": 0,
                "total_loans": 0,
                "repaid_loans": 0,
                "staking_tier": 0,
                "total_transactions": 0,
            }
            
            # Get score
            score_result = await session.execute(
                select(Score).where(Score.wallet_address == address)
            )
            score = score_result.scalar_one_or_none()
            if score:
                stats["has_score"] = True
                stats["current_score"] = score.score
            
            # Get loans
            loans_result = await session.execute(
                select(Loan).where(Loan.borrower_address == address)
            )
            loans = loans_result.scalars().all()
            stats["total_loans"] = len(loans)
            stats["repaid_loans"] = len([l for l in loans if l.status == "repaid"])
            
            # Get staking tier
            staking_service = StakingService()
            stats["staking_tier"] = staking_service.get_integration_tier(address)
            
            # Get transaction count
            tx_result = await session.execute(
                select(Transaction).where(Transaction.from_address == address)
            )
            transactions = tx_result.scalars().all()
            stats["total_transactions"] = len(transactions)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting user stats: {e}", exc_info=True)
            return {}
    
    async def _unlock_achievement(
        self,
        address: str,
        achievement_id: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Unlock an achievement for user"""
        try:
            # Ensure achievement exists in database
            achievement_result = await session.execute(
                select(Achievement).where(Achievement.achievement_id == achievement_id)
            )
            achievement = achievement_result.scalar_one_or_none()
            
            if not achievement:
                # Create achievement if it doesn't exist
                achievement_def = self.ACHIEVEMENTS.get(achievement_id)
                if not achievement_def:
                    return None
                
                achievement = Achievement(
                    achievement_id=achievement_id,
                    name=achievement_def["name"],
                    description=achievement_def["description"],
                    icon=achievement_def.get("icon", "🏅"),
                    category=achievement_def.get("category", "general"),
                )
                session.add(achievement)
                await session.flush()
            
            # Check if user already has this achievement
            user_achievement_result = await session.execute(
                select(UserAchievement).where(
                    and_(
                        UserAchievement.wallet_address == address,
                        UserAchievement.achievement_id == achievement_id
                    )
                )
            )
            existing = user_achievement_result.scalar_one_or_none()
            
            if existing:
                return None  # Already unlocked
            
            # Create user achievement
            user_achievement = UserAchievement(
                wallet_address=address,
                achievement_id=achievement_id,
                unlocked_at=datetime.utcnow()
            )
            session.add(user_achievement)
            await session.commit()
            
            logger.info(f"Unlocked achievement {achievement_id} for {address}")
            
            return {
                "achievement_id": achievement_id,
                "name": achievement.name,
                "description": achievement.description,
                "icon": achievement.icon,
                "unlocked_at": user_achievement.unlocked_at.isoformat() if user_achievement.unlocked_at else None,
            }
        except Exception as e:
            logger.error(f"Error unlocking achievement: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def get_user_badges(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get user's unlocked badges
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of badge dicts
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._get_user_badges(address, db_session)
            else:
                return await self._get_user_badges(address, session)
        except Exception as e:
            logger.error(f"Error getting user badges: {e}", exc_info=True)
            return []
    
    async def _get_user_badges(
        self,
        address: str,
        session
    ) -> List[Dict[str, Any]]:
        """Get user badges from database"""
        try:
            result = await session.execute(
                select(UserAchievement, Achievement)
                .join(Achievement, UserAchievement.achievement_id == Achievement.achievement_id)
                .where(UserAchievement.wallet_address == address)
                .order_by(UserAchievement.unlocked_at.desc())
            )
            rows = result.all()
            
            return [
                {
                    "achievement_id": ua.achievement_id,
                    "name": a.name,
                    "description": a.description,
                    "icon": a.icon,
                    "category": a.category,
                    "unlocked_at": ua.unlocked_at.isoformat() if ua.unlocked_at else None,
                }
                for ua, a in rows
            ]
        except Exception as e:
            logger.error(f"Error in _get_user_badges: {e}", exc_info=True)
            return []
    
    async def get_achievement_list(
        self,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get all available achievements
        
        Args:
            session: Database session (optional)
            
        Returns:
            List of achievement dicts
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._get_achievement_list(db_session)
            else:
                return await self._get_achievement_list(session)
        except Exception as e:
            logger.error(f"Error getting achievement list: {e}", exc_info=True)
            return []
    
    async def _get_achievement_list(
        self,
        session
    ) -> List[Dict[str, Any]]:
        """Get all achievements from database"""
        try:
            result = await session.execute(select(Achievement))
            achievements = result.scalars().all()
            
            return [
                {
                    "achievement_id": a.achievement_id,
                    "name": a.name,
                    "description": a.description,
                    "icon": a.icon,
                    "category": a.category,
                }
                for a in achievements
            ]
        except Exception as e:
            logger.error(f"Error in _get_achievement_list: {e}", exc_info=True)
            return []


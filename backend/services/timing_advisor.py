"""
Timing advisor service for optimal borrowing timing suggestions
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime, timedelta
from utils.logger import get_logger
from services.scoring import ScoringService
from services.oracle import QIEOracleService
from database.repositories import ScoreHistoryRepository

logger = get_logger(__name__)


class TimingAdvisor:
    """Service for suggesting optimal borrowing timing"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.oracle_service = QIEOracleService()
    
    async def suggest_borrowing_timing(
        self,
        address: str,
        desired_amount: Decimal,
        session=None
    ) -> Dict[str, Any]:
        """
        Suggest best time to borrow
        
        Args:
            address: Wallet address
            desired_amount: Desired loan amount
            session: Database session (optional)
            
        Returns:
            Timing recommendation dict
        """
        try:
            # Analyze current conditions
            current_conditions = await self.analyze_market_conditions()
            
            # Get user's score and trend
            score_result = await self.scoring_service.compute_score(address)
            current_score = score_result.get('score', 500)
            
            # Get score history for trend
            from database.connection import get_session
            
            if session is None:
                async with get_session() as db_session:
                    history = await ScoreHistoryRepository.get_history(
                        db_session, address, limit=30
                    )
            else:
                history = await ScoreHistoryRepository.get_history(session, address, limit=30)
            
            # Calculate score trend
            score_trend = 0
            if len(history) >= 2:
                oldest_score = history[-1].score
                newest_score = history[0].score
                score_trend = newest_score - oldest_score
            
            # Calculate timing score
            timing_score = self._calculate_timing_score(
                current_score,
                score_trend,
                current_conditions
            )
            
            # Determine recommendation
            if timing_score >= 0.8:
                recommendation = "excellent"
                message = "Current conditions are excellent for borrowing. Consider borrowing now."
            elif timing_score >= 0.6:
                recommendation = "good"
                message = "Current conditions are good for borrowing. This is a favorable time."
            elif timing_score >= 0.4:
                recommendation = "moderate"
                message = "Current conditions are moderate. Consider waiting for better conditions."
            else:
                recommendation = "poor"
                message = "Current conditions are not ideal. Consider waiting for improved conditions."
            
            # Suggest specific timing
            suggested_timing = self._suggest_specific_timing(
                timing_score,
                score_trend,
                current_conditions
            )
            
            return {
                "current_timing_score": timing_score,
                "recommendation": recommendation,
                "message": message,
                "current_score": current_score,
                "score_trend": score_trend,
                "market_conditions": current_conditions,
                "suggested_timing": suggested_timing,
                "factors": {
                    "score_factor": self._score_factor(current_score),
                    "trend_factor": self._trend_factor(score_trend),
                    "volatility_factor": self._volatility_factor(current_conditions.get('volatility', 0.2)),
                },
            }
        except Exception as e:
            logger.error(f"Error suggesting borrowing timing: {e}", exc_info=True)
            return {
                "current_timing_score": 0.5,
                "recommendation": "unknown",
                "message": "Unable to analyze timing",
            }
    
    async def analyze_market_conditions(
        self
    ) -> Dict[str, Any]:
        """
        Analyze current market conditions
        
        Returns:
            Market conditions dict
        """
        try:
            # Get volatility
            volatility = await self.oracle_service.get_volatility('ETH', days=7) or 0.2
            
            # Determine market condition
            if volatility < 0.1:
                condition = "stable"
            elif volatility < 0.3:
                condition = "moderate"
            else:
                condition = "volatile"
            
            return {
                "volatility": volatility,
                "condition": condition,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}", exc_info=True)
            return {
                "volatility": 0.2,
                "condition": "unknown",
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def get_timing_score(
        self,
        date_range: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Score timing quality for a date range
        
        Args:
            date_range: Optional date range dict with 'start' and 'end'
            
        Returns:
            Timing score dict
        """
        try:
            # For now, analyze current conditions
            # In production, would analyze historical data for date range
            conditions = await self.analyze_market_conditions()
            
            base_score = 0.5
            
            # Adjust based on volatility
            volatility = conditions.get('volatility', 0.2)
            if volatility < 0.1:
                base_score += 0.3  # Low volatility = good timing
            elif volatility < 0.3:
                base_score += 0.1
            else:
                base_score -= 0.2  # High volatility = poor timing
            
            return {
                "timing_score": max(0.0, min(1.0, base_score)),
                "market_conditions": conditions,
                "explanation": self._explain_timing_score(base_score, conditions),
            }
        except Exception as e:
            logger.error(f"Error getting timing score: {e}", exc_info=True)
            return {
                "timing_score": 0.5,
                "explanation": "Unable to calculate timing score",
            }
    
    def _calculate_timing_score(
        self,
        score: int,
        score_trend: int,
        market_conditions: Dict[str, Any]
    ) -> float:
        """Calculate overall timing score (0-1)"""
        timing_score = 0.5  # Base score
        
        # Score factor (higher is better)
        score_factor = self._score_factor(score)
        timing_score += score_factor * 0.3
        
        # Trend factor (increasing is better)
        trend_factor = self._trend_factor(score_trend)
        timing_score += trend_factor * 0.2
        
        # Volatility factor (lower is better)
        volatility = market_conditions.get('volatility', 0.2)
        volatility_factor = self._volatility_factor(volatility)
        timing_score += volatility_factor * 0.3
        
        return max(0.0, min(1.0, timing_score))
    
    def _score_factor(self, score: int) -> float:
        """Calculate score factor (0-1)"""
        if score >= 800:
            return 1.0
        elif score >= 600:
            return 0.7
        elif score >= 400:
            return 0.4
        else:
            return 0.2
    
    def _trend_factor(self, trend: int) -> float:
        """Calculate trend factor (0-1)"""
        if trend > 50:
            return 1.0  # Strong upward trend
        elif trend > 20:
            return 0.7  # Moderate upward trend
        elif trend > -20:
            return 0.5  # Stable
        elif trend > -50:
            return 0.3  # Moderate downward trend
        else:
            return 0.1  # Strong downward trend
    
    def _volatility_factor(self, volatility: float) -> float:
        """Calculate volatility factor (0-1, lower volatility = higher factor)"""
        if volatility < 0.1:
            return 1.0  # Very stable
        elif volatility < 0.2:
            return 0.8  # Stable
        elif volatility < 0.3:
            return 0.6  # Moderate
        elif volatility < 0.5:
            return 0.4  # High
        else:
            return 0.2  # Very high
    
    def _suggest_specific_timing(
        self,
        timing_score: float,
        score_trend: int,
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest specific timing (now, wait, etc.)"""
        volatility = market_conditions.get('volatility', 0.2)
        
        if timing_score >= 0.7:
            return {
                "action": "borrow_now",
                "reason": "Excellent conditions for borrowing",
                "wait_days": 0,
            }
        elif timing_score >= 0.5:
            if score_trend > 0:
                return {
                    "action": "borrow_now",
                    "reason": "Good conditions and improving score",
                    "wait_days": 0,
                }
            else:
                return {
                    "action": "wait",
                    "reason": "Consider waiting for score improvement",
                    "wait_days": 7,
                }
        else:
            if volatility > 0.5:
                return {
                    "action": "wait",
                    "reason": "High market volatility - wait for stability",
                    "wait_days": 14,
                }
            elif score_trend < -20:
                return {
                    "action": "wait",
                    "reason": "Score is declining - wait for recovery",
                    "wait_days": 30,
                }
            else:
                return {
                    "action": "wait",
                    "reason": "Conditions not ideal - wait for improvement",
                    "wait_days": 7,
                }
    
    def _explain_timing_score(
        self,
        score: float,
        conditions: Dict[str, Any]
    ) -> str:
        """Generate explanation for timing score"""
        volatility = conditions.get('volatility', 0.2)
        condition = conditions.get('condition', 'unknown')
        
        explanation = f"Timing score: {score:.1%}. "
        
        if score >= 0.7:
            explanation += "Excellent timing - market is stable and conditions are favorable."
        elif score >= 0.5:
            explanation += f"Good timing - market is {condition}."
        else:
            explanation += f"Poor timing - market is {condition} with high volatility ({volatility:.1%})."
        
        return explanation


"""
Seasonal adjustment service for market volatility and seasonal score adjustments
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from utils.logger import get_logger
from services.oracle import QIEOracleService

logger = get_logger(__name__)


class SeasonalAdjuster:
    """Service for calculating seasonal and market volatility adjustments"""
    
    # Seasonal factors (month-based adjustments)
    SEASONAL_FACTORS = {
        1: 1.0,   # January - neutral
        2: 1.0,   # February - neutral
        3: 0.98,  # March - slight negative (Q1 end)
        4: 1.0,   # April - neutral
        5: 1.0,   # May - neutral
        6: 0.97,  # June - slight negative (mid-year volatility)
        7: 1.0,   # July - neutral
        8: 1.0,   # August - neutral
        9: 0.98,  # September - slight negative (Q3 end)
        10: 1.0,  # October - neutral
        11: 1.02, # November - slight positive (year-end)
        12: 1.03, # December - positive (holiday season, year-end)
    }
    
    # Volatility thresholds
    LOW_VOLATILITY_THRESHOLD = 0.1
    MEDIUM_VOLATILITY_THRESHOLD = 0.3
    HIGH_VOLATILITY_THRESHOLD = 0.5
    
    # Adjustment ranges
    MAX_VOLATILITY_ADJUSTMENT = -20  # Maximum penalty during high volatility
    MAX_SEASONAL_ADJUSTMENT = 5      # Maximum seasonal boost
    
    def __init__(self):
        self.oracle_service = QIEOracleService()
    
    async def get_market_volatility(self, days: int = 30) -> float:
        """
        Get current market volatility
        
        Args:
            days: Number of days to look back
            
        Returns:
            Volatility value (0-1)
        """
        try:
            volatility = await self.oracle_service.get_volatility('ETH', days=days)
            return volatility if volatility else 0.2  # Default to medium volatility
        except Exception as e:
            logger.error(f"Error getting market volatility: {e}", exc_info=True)
            return 0.2  # Default to medium volatility
    
    def get_seasonal_factor(self, date: Optional[datetime] = None) -> float:
        """
        Get seasonal adjustment factor
        
        Args:
            date: Date to check (defaults to now)
            
        Returns:
            Seasonal factor (multiplier)
        """
        if date is None:
            date = datetime.utcnow()
        
        month = date.month
        return self.SEASONAL_FACTORS.get(month, 1.0)
    
    async def calculate_seasonal_adjustment(
        self,
        base_score: int,
        date: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        Calculate seasonal adjustment
        
        Args:
            base_score: Base credit score
            date: Date to calculate for (defaults to now)
            
        Returns:
            Adjustment dict with factor, adjustment amount, and explanation
        """
        try:
            seasonal_factor = self.get_seasonal_factor(date)
            seasonal_adjustment = int((seasonal_factor - 1.0) * 10)  # Scale to points
            
            # Cap adjustment
            seasonal_adjustment = max(
                -self.MAX_SEASONAL_ADJUSTMENT,
                min(self.MAX_SEASONAL_ADJUSTMENT, seasonal_adjustment)
            )
            
            explanation = self._get_seasonal_explanation(date, seasonal_factor)
            
            return {
                "factor": seasonal_factor,
                "adjustment": seasonal_adjustment,
                "explanation": explanation,
            }
        except Exception as e:
            logger.error(f"Error calculating seasonal adjustment: {e}", exc_info=True)
            return {
                "factor": 1.0,
                "adjustment": 0,
                "explanation": "Seasonal adjustment unavailable",
            }
    
    async def calculate_volatility_adjustment(
        self,
        base_score: int,
        days: int = 30
    ) -> Dict[str, any]:
        """
        Calculate volatility-based adjustment
        
        Args:
            base_score: Base credit score
            days: Days to look back for volatility
            
        Returns:
            Adjustment dict with volatility, adjustment amount, and explanation
        """
        try:
            volatility = await self.get_market_volatility(days)
            
            # Calculate adjustment based on volatility
            if volatility < self.LOW_VOLATILITY_THRESHOLD:
                adjustment = 0  # No penalty for low volatility
                level = "low"
            elif volatility < self.MEDIUM_VOLATILITY_THRESHOLD:
                adjustment = -5  # Small penalty
                level = "medium"
            elif volatility < self.HIGH_VOLATILITY_THRESHOLD:
                adjustment = -10  # Moderate penalty
                level = "high"
            else:
                adjustment = self.MAX_VOLATILITY_ADJUSTMENT  # Maximum penalty
                level = "very_high"
            
            explanation = f"Market volatility is {level} ({volatility:.2%}), resulting in a {abs(adjustment)} point adjustment."
            
            return {
                "volatility": volatility,
                "adjustment": adjustment,
                "level": level,
                "explanation": explanation,
            }
        except Exception as e:
            logger.error(f"Error calculating volatility adjustment: {e}", exc_info=True)
            return {
                "volatility": 0.2,
                "adjustment": 0,
                "level": "unknown",
                "explanation": "Volatility adjustment unavailable",
            }
    
    async def calculate_seasonal_adjustment_combined(
        self,
        base_score: int,
        date: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        Calculate combined seasonal and volatility adjustment
        
        Args:
            base_score: Base credit score
            date: Date to calculate for (defaults to now)
            
        Returns:
            Combined adjustment information
        """
        try:
            seasonal = await self.calculate_seasonal_adjustment(base_score, date)
            volatility = await self.calculate_volatility_adjustment(base_score)
            
            total_adjustment = seasonal["adjustment"] + volatility["adjustment"]
            
            return {
                "seasonal": seasonal,
                "volatility": volatility,
                "total_adjustment": total_adjustment,
                "explanation": f"{seasonal['explanation']} {volatility['explanation']}",
            }
        except Exception as e:
            logger.error(f"Error calculating combined adjustment: {e}", exc_info=True)
            return {
                "seasonal": {"adjustment": 0},
                "volatility": {"adjustment": 0},
                "total_adjustment": 0,
                "explanation": "Adjustment calculation unavailable",
            }
    
    def _get_seasonal_explanation(self, date: datetime, factor: float) -> str:
        """Get human-readable seasonal explanation"""
        month_name = date.strftime("%B")
        
        if factor > 1.0:
            return f"Seasonal factor for {month_name}: +{int((factor - 1.0) * 10)} points (positive seasonal trend)"
        elif factor < 1.0:
            return f"Seasonal factor for {month_name}: {int((factor - 1.0) * 10)} points (seasonal adjustment)"
        else:
            return f"Seasonal factor for {month_name}: neutral"


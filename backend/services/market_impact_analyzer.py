"""
Market impact analyzer service for analyzing market condition impact on credit
"""
from typing import Dict, List, Optional, Any
from utils.logger import get_logger
from services.scoring import ScoringService
from services.oracle import QIEOracleService
from services.portfolio_service import PortfolioService

logger = get_logger(__name__)


class MarketImpactAnalyzer:
    """Service for analyzing market impact on credit scores"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.oracle_service = QIEOracleService()
        self.portfolio_service = PortfolioService()
    
    async def analyze_market_impact_on_credit(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Analyze how market conditions affect user's credit
        
        Args:
            address: Wallet address
            
        Returns:
            Market impact analysis dict
        """
        try:
            # Get current market conditions
            market_conditions = await self._get_market_conditions()
            
            # Get user's portfolio
            portfolio = await self.portfolio_service.get_token_holdings(address)
            portfolio_value = sum(
                float(token.get('value_usd', 0))
                for token in portfolio.get('holdings', [])
            )
            
            # Get current score
            score_result = await self.scoring_service.compute_score(address)
            current_score = score_result.get('score', 500)
            
            # Calculate impact
            impact = self._calculate_market_impact(
                market_conditions,
                portfolio_value,
                current_score
            )
            
            # Get risk factors
            risk_factors = await self._get_market_risk_factors(market_conditions)
            
            return {
                "current_score": current_score,
                "portfolio_value": portfolio_value,
                "market_conditions": market_conditions,
                "impact_score": impact,
                "impact_level": self._impact_to_level(impact),
                "risk_factors": risk_factors,
                "recommendations": self._generate_recommendations(impact, risk_factors),
            }
        except Exception as e:
            logger.error(f"Error analyzing market impact: {e}", exc_info=True)
            return {
                "current_score": 0,
                "impact_score": 0,
                "impact_level": "unknown",
            }
    
    async def predict_score_impact(
        self,
        market_scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict score impact from market changes
        
        Args:
            market_scenario: Market scenario dict (volatility_change, price_change, etc.)
            
        Returns:
            Predicted impact dict
        """
        try:
            current_volatility = await self.oracle_service.get_volatility('ETH', days=7) or 0.2
            
            # Scenario volatility
            scenario_volatility = market_scenario.get('volatility', current_volatility)
            volatility_change = scenario_volatility - current_volatility
            
            # Calculate impact
            # Higher volatility = negative impact on score (via oracle penalty)
            volatility_impact = -abs(volatility_change) * 20  # Up to 20 points per 0.1 volatility change
            
            # Price change impact (if portfolio affected)
            price_change = market_scenario.get('price_change', 0)
            price_impact = 0  # Price changes don't directly affect score, but affect portfolio value
            
            total_impact = volatility_impact
            
            return {
                "predicted_score_change": int(total_impact),
                "volatility_impact": int(volatility_impact),
                "price_impact": int(price_impact),
                "scenario": market_scenario,
                "explanation": self._explain_predicted_impact(total_impact, volatility_change),
            }
        except Exception as e:
            logger.error(f"Error predicting score impact: {e}", exc_info=True)
            return {
                "predicted_score_change": 0,
                "explanation": "Unable to predict impact",
            }
    
    async def get_market_risk_factors(
        self,
        market_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get current market risk factors
        
        Args:
            market_conditions: Optional market conditions (will fetch if None)
            
        Returns:
            Risk factors dict
        """
        try:
            if not market_conditions:
                market_conditions = await self._get_market_conditions()
            
            volatility = market_conditions.get('volatility', 0.2)
            
            risk_factors = {
                "volatility": volatility,
                "volatility_level": self._volatility_to_level(volatility),
                "risk_score": self._calculate_risk_score(volatility),
            }
            
            return risk_factors
        except Exception as e:
            logger.error(f"Error getting market risk factors: {e}", exc_info=True)
            return {
                "volatility": 0.2,
                "volatility_level": "moderate",
                "risk_score": 0.5,
            }
    
    async def _get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions"""
        try:
            volatility = await self.oracle_service.get_volatility('ETH', days=7) or 0.2
            
            return {
                "volatility": volatility,
                "volatility_level": self._volatility_to_level(volatility),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting market conditions: {e}", exc_info=True)
            return {
                "volatility": 0.2,
                "volatility_level": "moderate",
            }
    
    def _calculate_market_impact(
        self,
        market_conditions: Dict[str, Any],
        portfolio_value: float,
        current_score: int
    ) -> float:
        """Calculate market impact score (0-1, higher = more positive impact)"""
        volatility = market_conditions.get('volatility', 0.2)
        
        # Lower volatility = positive impact
        if volatility < 0.1:
            impact = 0.9
        elif volatility < 0.2:
            impact = 0.7
        elif volatility < 0.3:
            impact = 0.5
        elif volatility < 0.5:
            impact = 0.3
        else:
            impact = 0.1
        
        # Portfolio value stability (simplified)
        if portfolio_value > 0:
            # Assume stable portfolio = positive
            impact += 0.1
        
        return min(1.0, max(0.0, impact))
    
    def _impact_to_level(self, impact: float) -> str:
        """Convert impact score to level"""
        if impact >= 0.7:
            return "positive"
        elif impact >= 0.4:
            return "neutral"
        else:
            return "negative"
    
    def _volatility_to_level(self, volatility: float) -> str:
        """Convert volatility to level"""
        if volatility < 0.1:
            return "very_low"
        elif volatility < 0.2:
            return "low"
        elif volatility < 0.3:
            return "moderate"
        elif volatility < 0.5:
            return "high"
        else:
            return "very_high"
    
    def _calculate_risk_score(self, volatility: float) -> float:
        """Calculate risk score (0-1, higher = more risk)"""
        # Higher volatility = higher risk
        if volatility < 0.1:
            return 0.1
        elif volatility < 0.2:
            return 0.3
        elif volatility < 0.3:
            return 0.5
        elif volatility < 0.5:
            return 0.7
        else:
            return 0.9
    
    def _get_market_risk_factors(
        self,
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get market risk factors"""
        volatility = market_conditions.get('volatility', 0.2)
        
        return {
            "volatility": volatility,
            "volatility_level": self._volatility_to_level(volatility),
            "risk_score": self._calculate_risk_score(volatility),
        }
    
    def _generate_recommendations(
        self,
        impact: float,
        risk_factors: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on impact"""
        recommendations = []
        
        volatility = risk_factors.get('volatility', 0.2)
        
        if volatility > 0.5:
            recommendations.append("High market volatility detected - consider waiting for stability")
            recommendations.append("Monitor your portfolio value closely")
        elif volatility > 0.3:
            recommendations.append("Moderate market volatility - proceed with caution")
        
        if impact < 0.4:
            recommendations.append("Market conditions may negatively impact your credit score")
            recommendations.append("Consider reducing exposure during volatile periods")
        
        if not recommendations:
            recommendations.append("Market conditions are favorable")
        
        return recommendations
    
    def _explain_predicted_impact(
        self,
        impact: float,
        volatility_change: float
    ) -> str:
        """Generate explanation for predicted impact"""
        if abs(impact) < 5:
            return "Market changes are predicted to have minimal impact on your credit score."
        
        direction = "decrease" if impact < 0 else "increase"
        
        explanation = f"Market changes are predicted to {direction} your credit score by approximately {abs(impact):.0f} points. "
        
        if abs(volatility_change) > 0.1:
            explanation += f"Volatility change of {volatility_change:.1%} contributes to this impact."
        
        return explanation


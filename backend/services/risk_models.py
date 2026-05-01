"""
Advanced Risk Models

Loan-type-specific risk, portfolio risk, market risk, and liquidity risk calculations.
"""

import os
from typing import Dict, Optional, Any
from services.ml_scoring import MLScoringService
from services.oracle import QIEOracleService
from services.feature_engineering import FeatureEngineering
from utils.logger import get_logger

logger = get_logger(__name__)


class RiskModelService:
    """Service for advanced risk modeling"""
    
    def __init__(self):
        self.ml_scoring = MLScoringService()
        self.oracle_service = QIEOracleService()
        self.feature_engineering = FeatureEngineering()
    
    async def calculate_loan_risk(
        self,
        address: str,
        loan_type: str,
        loan_amount: float,
        collateral_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate risk for a specific loan
        
        Args:
            address: Borrower address
            loan_type: Type of loan (uncollateralized, collateralized, flash)
            loan_amount: Loan amount
            collateral_value: Collateral value (if applicable)
            
        Returns:
            Risk assessment
        """
        try:
            # Get credit score
            score_result = await self.ml_scoring.compute_score(address)
            score = score_result.get("score", 500)
            risk_band = score_result.get("riskBand", 2)
            
            # Base risk from credit score
            base_risk = self._score_to_risk(score)
            
            # Loan type risk multiplier
            type_multipliers = {
                "uncollateralized": 2.0,  # High risk
                "collateralized": 0.5,    # Lower risk
                "flash": 3.0,              # Very high risk
            }
            type_multiplier = type_multipliers.get(loan_type, 1.0)
            
            # Collateral risk adjustment
            collateral_risk = 0.0
            if collateral_value:
                ltv = loan_amount / collateral_value if collateral_value > 0 else 1.0
                if ltv > 0.8:
                    collateral_risk = 0.3  # High LTV risk
                elif ltv > 0.6:
                    collateral_risk = 0.15
                else:
                    collateral_risk = 0.05
            
            # Portfolio risk
            portfolio_risk = await self._calculate_portfolio_risk(address)
            
            # Market risk
            market_risk = await self._calculate_market_risk()
            
            # Liquidity risk
            liquidity_risk = await self._calculate_liquidity_risk(address)
            
            # Combined risk score (0-1)
            combined_risk = (
                base_risk * 0.4 +
                (base_risk * type_multiplier * 0.3) +
                collateral_risk * 0.1 +
                portfolio_risk * 0.1 +
                market_risk * 0.05 +
                liquidity_risk * 0.05
            )
            
            combined_risk = min(1.0, combined_risk)
            
            # Calculate LTV recommendation
            recommended_ltv = self._calculate_recommended_ltv(combined_risk, loan_type)
            
            return {
                "address": address,
                "loan_type": loan_type,
                "combined_risk": combined_risk,
                "risk_level": self._risk_to_level(combined_risk),
                "base_risk": base_risk,
                "type_multiplier": type_multiplier,
                "collateral_risk": collateral_risk,
                "portfolio_risk": portfolio_risk,
                "market_risk": market_risk,
                "liquidity_risk": liquidity_risk,
                "recommended_ltv": recommended_ltv,
                "credit_score": score,
                "risk_band": risk_band,
            }
            
        except Exception as e:
            logger.error(f"Error calculating loan risk: {e}", exc_info=True)
            return {
                "address": address,
                "combined_risk": 0.5,
                "risk_level": "medium",
                "error": str(e),
            }
    
    def _score_to_risk(self, score: int) -> float:
        """Convert credit score to risk (0-1)"""
        # Lower score = higher risk
        return 1.0 - (score / 1000.0)
    
    def _risk_to_level(self, risk: float) -> str:
        """Convert risk score to level"""
        if risk >= 0.7:
            return "high"
        elif risk >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_recommended_ltv(self, risk: float, loan_type: str) -> float:
        """Calculate recommended LTV based on risk"""
        base_ltv = {
            "uncollateralized": 0.0,  # No LTV for uncollateralized
            "collateralized": 0.75,
            "flash": 0.0,  # No LTV for flash loans
        }.get(loan_type, 0.5)
        
        # Adjust based on risk
        if risk > 0.7:
            return base_ltv * 0.5  # Reduce LTV for high risk
        elif risk > 0.4:
            return base_ltv * 0.75
        else:
            return base_ltv
    
    async def _calculate_portfolio_risk(self, address: str) -> float:
        """Calculate portfolio diversification risk"""
        try:
            features = await self.feature_engineering.extract_all_features(address)
            
            # Diversification index (higher = better)
            diversification = features.get("diversification_index", 0.5)
            
            # Portfolio volatility (higher = riskier)
            volatility = features.get("portfolio_volatility", 0.3)
            
            # Combined portfolio risk
            portfolio_risk = (1.0 - diversification) * 0.5 + volatility * 0.5
            
            return min(1.0, portfolio_risk)
            
        except Exception as e:
            logger.warning(f"Error calculating portfolio risk: {e}")
            return 0.5  # Default medium risk
    
    async def _calculate_market_risk(self) -> float:
        """Calculate current market risk"""
        try:
            # Get market volatility
            volatility = await self.oracle_service.get_volatility('ETH', days=30)
            
            if volatility:
                # High volatility = high market risk
                market_risk = min(1.0, volatility)
            else:
                market_risk = 0.3  # Default moderate risk
            
            return market_risk
            
        except Exception as e:
            logger.warning(f"Error calculating market risk: {e}")
            return 0.3  # Default moderate risk
    
    async def _calculate_liquidity_risk(self, address: str) -> float:
        """Calculate liquidity risk (ability to liquidate positions)"""
        try:
            features = await self.feature_engineering.extract_all_features(address)
            
            # Check stablecoin ratio (higher = more liquid)
            stablecoin_ratio = features.get("stablecoin_ratio", 0.3)
            
            # Check token concentration (higher concentration = less liquid)
            token_concentration = features.get("token_concentration", 0.5)
            
            # Liquidity risk (inverse of liquidity)
            liquidity_risk = (1.0 - stablecoin_ratio) * 0.5 + token_concentration * 0.5
            
            return min(1.0, liquidity_risk)
            
        except Exception as e:
            logger.warning(f"Error calculating liquidity risk: {e}")
            return 0.5  # Default medium risk
    
    async def get_risk_profile(self, address: str) -> Dict[str, Any]:
        """Get comprehensive risk profile for an address"""
        try:
            score_result = await self.ml_scoring.compute_score(address)
            features = await self.feature_engineering.extract_all_features(address)
            
            portfolio_risk = await self._calculate_portfolio_risk(address)
            market_risk = await self._calculate_market_risk()
            liquidity_risk = await self._calculate_liquidity_risk(address)
            
            return {
                "address": address,
                "credit_score": score_result.get("score", 500),
                "risk_band": score_result.get("riskBand", 2),
                "portfolio_risk": portfolio_risk,
                "market_risk": market_risk,
                "liquidity_risk": liquidity_risk,
                "overall_risk": (portfolio_risk + market_risk + liquidity_risk) / 3,
                "features": {
                    "diversification": features.get("diversification_index", 0.5),
                    "volatility": features.get("portfolio_volatility", 0.3),
                    "stablecoin_ratio": features.get("stablecoin_ratio", 0.3),
                },
            }
            
        except Exception as e:
            logger.error(f"Error getting risk profile: {e}", exc_info=True)
            return {
                "address": address,
                "error": str(e),
            }


"""
Default probability predictor service for predicting loan default risk
"""
from typing import Dict, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from services.scoring import ScoringService
from services.loan_service import LoanService
from services.portfolio_service import PortfolioService

logger = get_logger(__name__)


class DefaultPredictor:
    """Service for predicting default probability"""
    
    # Risk factors and their weights
    RISK_FACTORS = {
        "credit_score": 0.30,  # 30% weight
        "score_trend": 0.15,   # 15% weight
        "existing_debt": 0.20, # 20% weight
        "portfolio_value": 0.15, # 15% weight
        "transaction_frequency": 0.10, # 10% weight
        "market_volatility": 0.10, # 10% weight
    }
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.loan_service = LoanService()
        self.portfolio_service = PortfolioService()
    
    async def predict_default_probability(
        self,
        address: str,
        loan_amount: Decimal,
        term_days: int,
        session=None
    ) -> Dict[str, Any]:
        """
        Predict default probability for a loan
        
        Args:
            address: Borrower address
            loan_amount: Loan amount
            term_days: Loan term in days
            session: Database session (optional)
            
        Returns:
            Prediction dict with probability, confidence, and risk factors
        """
        try:
            # Get risk factors
            risk_factors = await self.get_risk_factors(address, loan_amount, session)
            
            # Calculate base probability from credit score
            score = risk_factors.get('credit_score', 500)
            base_probability = self._score_to_default_probability(score)
            
            # Adjust based on other factors
            adjustments = []
            
            # Score trend adjustment
            score_trend = risk_factors.get('score_trend', 0)
            if score_trend < -50:
                adjustments.append(0.15)  # Increase probability by 15%
            elif score_trend < -20:
                adjustments.append(0.08)
            elif score_trend > 20:
                adjustments.append(-0.05)  # Decrease probability by 5%
            
            # Debt ratio adjustment
            debt_ratio = risk_factors.get('debt_ratio', 0)
            if debt_ratio > 0.7:
                adjustments.append(0.20)  # High debt = higher default risk
            elif debt_ratio > 0.5:
                adjustments.append(0.10)
            elif debt_ratio < 0.3:
                adjustments.append(-0.05)  # Low debt = lower risk
            
            # Portfolio value adjustment
            portfolio_value = risk_factors.get('portfolio_value', 0)
            loan_to_portfolio = float(loan_amount) / portfolio_value if portfolio_value > 0 else 1.0
            if loan_to_portfolio > 0.5:
                adjustments.append(0.15)  # Loan > 50% of portfolio = higher risk
            elif loan_to_portfolio < 0.2:
                adjustments.append(-0.05)  # Loan < 20% of portfolio = lower risk
            
            # Transaction frequency adjustment
            tx_frequency = risk_factors.get('transaction_frequency', 0)
            if tx_frequency < 1:  # Less than 1 tx per day
                adjustments.append(0.10)  # Low activity = higher risk
            elif tx_frequency > 5:
                adjustments.append(-0.05)  # High activity = lower risk
            
            # Market volatility adjustment
            market_volatility = risk_factors.get('market_volatility', 0.2)
            if market_volatility > 0.5:
                adjustments.append(0.10)  # High volatility = higher risk
            
            # Calculate final probability
            total_adjustment = sum(adjustments)
            final_probability = base_probability + total_adjustment
            
            # Clamp to 0-1 range
            final_probability = max(0.0, min(1.0, final_probability))
            
            # Calculate confidence
            confidence = self._calculate_confidence(risk_factors)
            
            # Determine risk level
            if final_probability < 0.1:
                risk_level = "low"
            elif final_probability < 0.3:
                risk_level = "moderate"
            elif final_probability < 0.5:
                risk_level = "high"
            else:
                risk_level = "very_high"
            
            return {
                "default_probability": final_probability,
                "confidence": confidence,
                "risk_level": risk_level,
                "base_probability": base_probability,
                "adjustments": {
                    "score_trend": adjustments[0] if len(adjustments) > 0 else 0,
                    "debt_ratio": adjustments[1] if len(adjustments) > 1 else 0,
                    "portfolio_ratio": adjustments[2] if len(adjustments) > 2 else 0,
                    "transaction_frequency": adjustments[3] if len(adjustments) > 3 else 0,
                    "market_volatility": adjustments[4] if len(adjustments) > 4 else 0,
                },
                "risk_factors": risk_factors,
                "explanation": self._generate_explanation(final_probability, risk_level, risk_factors),
            }
        except Exception as e:
            logger.error(f"Error predicting default probability: {e}", exc_info=True)
            return {
                "default_probability": 0.5,
                "confidence": 0.0,
                "risk_level": "unknown",
                "explanation": "Unable to calculate default probability",
            }
    
    async def get_risk_factors(
        self,
        address: str,
        loan_amount: Decimal,
        session=None
    ) -> Dict[str, Any]:
        """
        Get factors contributing to default risk
        
        Args:
            address: Wallet address
            loan_amount: Loan amount
            session: Database session (optional)
            
        Returns:
            Risk factors dict
        """
        try:
            # Get credit score
            score_result = await self.scoring_service.compute_score(address)
            score = score_result.get('score', 500)
            
            # Get score history for trend
            from database.connection import get_session
            from database.repositories import ScoreHistoryRepository
            from datetime import datetime, timedelta
            
            if session is None:
                async with get_session() as db_session:
                    history = await ScoreHistoryRepository.get_history(
                        db_session, address, limit=10
                    )
            else:
                history = await ScoreHistoryRepository.get_history(session, address, limit=10)
            
            score_trend = 0
            if len(history) >= 2:
                oldest_score = history[-1].score
                newest_score = history[0].score
                score_trend = newest_score - oldest_score
            
            # Get existing loans
            existing_loans = await self.loan_service.get_user_loans(address)
            total_debt = sum(
                Decimal(str(loan.get('principal_amount', 0)))
                for loan in existing_loans
                if loan.get('status') in ['active', 'pending']
            )
            
            # Get portfolio value
            portfolio = await self.portfolio_service.get_token_holdings(address)
            portfolio_value = sum(
                Decimal(str(token.get('value_usd', 0)))
                for token in portfolio.get('holdings', [])
            )
            
            # Calculate debt ratio
            debt_ratio = float(total_debt / portfolio_value) if portfolio_value > 0 else 0.0
            
            # Get transaction frequency (simplified)
            from database.repositories import TransactionRepository
            from datetime import datetime, timedelta
            
            if session is None:
                async with get_session() as db_session:
                    cutoff = datetime.utcnow() - timedelta(days=30)
                    recent_txs = await TransactionRepository.get_transactions_since(
                        db_session, address, cutoff
                    )
            else:
                cutoff = datetime.utcnow() - timedelta(days=30)
                recent_txs = await TransactionRepository.get_transactions_since(
                    session, address, cutoff
                )
            
            transaction_frequency = len(recent_txs) / 30.0  # Transactions per day
            
            # Get market volatility
            from services.oracle import QIEOracleService
            oracle = QIEOracleService()
            market_volatility = await oracle.get_volatility('ETH', days=7) or 0.2
            
            return {
                "credit_score": score,
                "score_trend": score_trend,
                "existing_debt": float(total_debt),
                "portfolio_value": float(portfolio_value),
                "debt_ratio": debt_ratio,
                "loan_amount": float(loan_amount),
                "transaction_frequency": transaction_frequency,
                "market_volatility": market_volatility,
            }
        except Exception as e:
            logger.error(f"Error getting risk factors: {e}", exc_info=True)
            return {
                "credit_score": 500,
                "score_trend": 0,
                "existing_debt": 0,
                "portfolio_value": 0,
                "debt_ratio": 0,
                "loan_amount": float(loan_amount),
                "transaction_frequency": 0,
                "market_volatility": 0.2,
            }
    
    def _score_to_default_probability(self, score: int) -> float:
        """Convert credit score to base default probability"""
        # Inverse relationship: higher score = lower probability
        # Score 0-1000 maps to probability 0.8-0.05
        if score >= 800:
            return 0.05
        elif score >= 600:
            return 0.10 + (800 - score) / 200 * 0.10  # 0.10-0.20
        elif score >= 400:
            return 0.20 + (600 - score) / 200 * 0.20  # 0.20-0.40
        else:
            return 0.40 + (400 - score) / 400 * 0.40  # 0.40-0.80
    
    def _calculate_confidence(
        self,
        risk_factors: Dict[str, Any]
    ) -> float:
        """Calculate confidence level (0-1) for prediction"""
        confidence = 0.5  # Base confidence
        
        # More data = higher confidence
        if risk_factors.get('portfolio_value', 0) > 0:
            confidence += 0.2
        
        if risk_factors.get('score_trend') is not None:
            confidence += 0.15
        
        if risk_factors.get('transaction_frequency', 0) > 0:
            confidence += 0.15
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_explanation(
        self,
        probability: float,
        risk_level: str,
        risk_factors: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation"""
        score = risk_factors.get('credit_score', 500)
        debt_ratio = risk_factors.get('debt_ratio', 0)
        
        explanation = f"Based on your credit score of {score} and current financial profile, "
        explanation += f"the predicted default probability is {probability:.1%} ({risk_level} risk). "
        
        if debt_ratio > 0.7:
            explanation += "High debt ratio increases default risk. "
        elif debt_ratio < 0.3:
            explanation += "Low debt ratio reduces default risk. "
        
        if score < 500:
            explanation += "Consider improving your credit score to reduce default risk."
        
        return explanation


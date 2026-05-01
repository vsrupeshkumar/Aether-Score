"""
Loan recommendation service for AI-powered loan suggestions
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from services.scoring import ScoringService
from services.portfolio_service import PortfolioService
from services.loan_service import LoanService

logger = get_logger(__name__)


class LoanRecommender:
    """Service for AI-powered loan recommendations"""
    
    # Maximum loan amount as percentage of portfolio
    MAX_PORTFOLIO_PERCENTAGE = 0.30  # 30% of portfolio value
    
    # Debt-to-income equivalent thresholds
    SAFE_DEBT_RATIO = 0.30  # 30% of portfolio
    MODERATE_DEBT_RATIO = 0.50  # 50% of portfolio
    HIGH_DEBT_RATIO = 0.70  # 70% of portfolio
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.portfolio_service = PortfolioService()
        self.loan_service = LoanService()
    
    async def recommend_loan_amount(
        self,
        address: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend optimal loan amount for a user
        
        Args:
            address: Wallet address
            constraints: Optional constraints (min_amount, max_amount, purpose)
            
        Returns:
            Recommendation dict with amount, reasoning, and confidence
        """
        try:
            constraints = constraints or {}
            
            # Get user's credit score
            score_result = await self.scoring_service.compute_score(address)
            score = score_result.get('score', 500)
            risk_band = score_result.get('riskBand', 2)
            
            # Get portfolio value
            portfolio = await self.portfolio_service.get_token_holdings(address)
            portfolio_value = sum(
                Decimal(str(token.get('value_usd', 0)))
                for token in portfolio.get('holdings', [])
            )
            
            # Get existing loans
            existing_loans = await self.loan_service.get_user_loans(address)
            total_debt = sum(
                Decimal(str(loan.get('principal_amount', 0)))
                for loan in existing_loans
                if loan.get('status') in ['active', 'pending']
            )
            
            # Calculate affordability
            affordability = await self.calculate_affordability(address)
            max_affordable = Decimal(str(affordability.get('max_loan_amount', 0)))
            
            # Calculate recommended amount based on score and portfolio
            recommended_amount = self._calculate_recommended_amount(
                score,
                risk_band,
                portfolio_value,
                total_debt,
                max_affordable,
                constraints
            )
            
            # Generate reasoning
            reasoning = self._generate_amount_reasoning(
                score,
                risk_band,
                portfolio_value,
                total_debt,
                recommended_amount,
                max_affordable
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(score, portfolio_value, total_debt)
            
            return {
                "recommended_amount": float(recommended_amount),
                "max_affordable": float(max_affordable),
                "current_debt": float(total_debt),
                "portfolio_value": float(portfolio_value),
                "credit_score": score,
                "risk_band": risk_band,
                "reasoning": reasoning,
                "confidence": confidence,
                "constraints_applied": constraints,
            }
        except Exception as e:
            logger.error(f"Error recommending loan amount: {e}", exc_info=True)
            return {
                "recommended_amount": 0,
                "max_affordable": 0,
                "reasoning": "Unable to generate recommendation due to error",
                "confidence": 0.0,
            }
    
    async def recommend_loan_terms(
        self,
        address: str,
        amount: Decimal
    ) -> Dict[str, Any]:
        """
        Recommend optimal loan terms (interest rate, duration)
        
        Args:
            address: Wallet address
            amount: Loan amount
            
        Returns:
            Recommendation dict with terms and reasoning
        """
        try:
            # Get user's credit score
            score_result = await self.scoring_service.compute_score(address)
            score = score_result.get('score', 500)
            risk_band = score_result.get('riskBand', 2)
            
            # Calculate recommended interest rate based on score
            recommended_rate = self._calculate_recommended_rate(score, risk_band)
            
            # Calculate recommended term based on amount and score
            recommended_term = self._calculate_recommended_term(amount, score, risk_band)
            
            # Generate reasoning
            reasoning = self._generate_terms_reasoning(
                score,
                risk_band,
                recommended_rate,
                recommended_term
            )
            
            return {
                "recommended_interest_rate": float(recommended_rate),
                "recommended_term_days": recommended_term,
                "credit_score": score,
                "risk_band": risk_band,
                "reasoning": reasoning,
                "estimated_monthly_payment": float(self._calculate_monthly_payment(amount, recommended_rate, recommended_term)),
            }
        except Exception as e:
            logger.error(f"Error recommending loan terms: {e}", exc_info=True)
            return {
                "recommended_interest_rate": 0.0,
                "recommended_term_days": 0,
                "reasoning": "Unable to generate recommendation due to error",
            }
    
    async def calculate_affordability(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Calculate borrowing capacity for a user
        
        Args:
            address: Wallet address
            
        Returns:
            Affordability dict with max loan amount and debt ratios
        """
        try:
            # Get portfolio value
            portfolio = await self.portfolio_service.get_token_holdings(address)
            portfolio_value = sum(
                Decimal(str(token.get('value_usd', 0)))
                for token in portfolio.get('holdings', [])
            )
            
            # Get existing loans
            existing_loans = await self.loan_service.get_user_loans(address)
            total_debt = sum(
                Decimal(str(loan.get('principal_amount', 0)))
                for loan in existing_loans
                if loan.get('status') in ['active', 'pending']
            )
            
            # Get credit score
            score_result = await self.scoring_service.compute_score(address)
            score = score_result.get('score', 500)
            risk_band = score_result.get('riskBand', 2)
            
            # Calculate max loan amount
            # Base: 30% of portfolio, adjusted by credit score
            base_max = portfolio_value * Decimal(str(self.MAX_PORTFOLIO_PERCENTAGE))
            
            # Adjust by credit score (higher score = higher multiplier)
            score_multiplier = Decimal(str(score)) / Decimal('1000')  # 0-1 range
            score_multiplier = max(Decimal('0.5'), min(Decimal('1.5'), score_multiplier))  # Cap between 0.5x and 1.5x
            
            max_loan_amount = base_max * score_multiplier
            
            # Subtract existing debt
            available_capacity = max(Decimal('0'), max_loan_amount - total_debt)
            
            # Calculate debt ratios
            current_debt_ratio = float(total_debt / portfolio_value) if portfolio_value > 0 else 0.0
            max_debt_ratio = float(max_loan_amount / portfolio_value) if portfolio_value > 0 else 0.0
            
            # Determine affordability level
            if current_debt_ratio < self.SAFE_DEBT_RATIO:
                affordability_level = "excellent"
            elif current_debt_ratio < self.MODERATE_DEBT_RATIO:
                affordability_level = "good"
            elif current_debt_ratio < self.HIGH_DEBT_RATIO:
                affordability_level = "moderate"
            else:
                affordability_level = "limited"
            
            return {
                "max_loan_amount": float(max_loan_amount),
                "available_capacity": float(available_capacity),
                "current_debt": float(total_debt),
                "portfolio_value": float(portfolio_value),
                "current_debt_ratio": current_debt_ratio,
                "max_debt_ratio": max_debt_ratio,
                "affordability_level": affordability_level,
                "credit_score": score,
                "risk_band": risk_band,
            }
        except Exception as e:
            logger.error(f"Error calculating affordability: {e}", exc_info=True)
            return {
                "max_loan_amount": 0,
                "available_capacity": 0,
                "current_debt": 0,
                "portfolio_value": 0,
                "affordability_level": "unknown",
            }
    
    def get_recommendation_reasons(
        self,
        address: str,
        recommendation: Dict[str, Any]
    ) -> List[str]:
        """
        Get detailed reasons for a recommendation
        
        Args:
            address: Wallet address
            recommendation: Recommendation dict
            
        Returns:
            List of reason strings
        """
        reasons = []
        
        score = recommendation.get('credit_score', 500)
        risk_band = recommendation.get('risk_band', 2)
        portfolio_value = recommendation.get('portfolio_value', 0)
        current_debt = recommendation.get('current_debt', 0)
        recommended_amount = recommendation.get('recommended_amount', 0)
        
        # Score-based reasons
        if score >= 800:
            reasons.append("Excellent credit score qualifies you for the best loan terms")
        elif score >= 600:
            reasons.append("Good credit score provides access to competitive rates")
        else:
            reasons.append("Consider improving your credit score for better loan terms")
        
        # Portfolio-based reasons
        if portfolio_value > 0:
            debt_ratio = current_debt / portfolio_value if portfolio_value > 0 else 0
            if debt_ratio < self.SAFE_DEBT_RATIO:
                reasons.append("Low current debt ratio indicates strong borrowing capacity")
            elif debt_ratio > self.HIGH_DEBT_RATIO:
                reasons.append("High debt ratio suggests limited additional borrowing capacity")
        
        # Amount-based reasons
        if recommended_amount > 0:
            reasons.append(f"Recommended amount of {recommended_amount:.2f} QIE balances risk and affordability")
        
        return reasons
    
    def _calculate_recommended_amount(
        self,
        score: int,
        risk_band: int,
        portfolio_value: Decimal,
        total_debt: Decimal,
        max_affordable: Decimal,
        constraints: Dict[str, Any]
    ) -> Decimal:
        """Calculate recommended loan amount"""
        # Start with max affordable
        recommended = max_affordable
        
        # Apply constraints
        if 'min_amount' in constraints:
            recommended = max(recommended, Decimal(str(constraints['min_amount'])))
        if 'max_amount' in constraints:
            recommended = min(recommended, Decimal(str(constraints['max_amount'])))
        
        # Adjust based on risk band (lower risk = can borrow more)
        risk_multipliers = {1: 1.0, 2: 0.8, 3: 0.6}
        risk_multiplier = risk_multipliers.get(risk_band, 0.8)
        recommended = recommended * Decimal(str(risk_multiplier))
        
        # Ensure positive
        return max(Decimal('0'), recommended)
    
    def _calculate_recommended_rate(
        self,
        score: int,
        risk_band: int
    ) -> Decimal:
        """Calculate recommended interest rate based on score"""
        # Base rates by risk band
        base_rates = {1: 5.0, 2: 10.0, 3: 15.0}
        base_rate = base_rates.get(risk_band, 10.0)
        
        # Adjust based on score within band
        if risk_band == 1:
            # Score 800-1000: 3-7% range
            rate = 3.0 + (1000 - score) / 1000 * 4.0
        elif risk_band == 2:
            # Score 500-799: 7-15% range
            rate = 7.0 + (799 - score) / 299 * 8.0
        else:
            # Score 0-499: 15-25% range
            rate = 15.0 + (499 - score) / 499 * 10.0
        
        return Decimal(str(max(3.0, min(25.0, rate))))
    
    def _calculate_recommended_term(
        self,
        amount: Decimal,
        score: int,
        risk_band: int
    ) -> int:
        """Calculate recommended loan term in days"""
        # Base terms by risk band
        base_terms = {1: 180, 2: 90, 3: 60}  # days
        base_term = base_terms.get(risk_band, 90)
        
        # Adjust based on amount (larger loans = longer terms)
        if amount > Decimal('10000'):
            base_term = int(base_term * 1.5)
        elif amount > Decimal('5000'):
            base_term = int(base_term * 1.2)
        
        # Cap between 30 and 365 days
        return max(30, min(365, base_term))
    
    def _calculate_monthly_payment(
        self,
        principal: Decimal,
        rate: Decimal,
        term_days: int
    ) -> Decimal:
        """Calculate monthly payment (simplified)"""
        # Simple interest calculation
        annual_rate = rate / Decimal('100')
        term_years = Decimal(str(term_days)) / Decimal('365')
        interest = principal * annual_rate * term_years
        total = principal + interest
        months = Decimal(str(term_days)) / Decimal('30')
        return total / months if months > 0 else Decimal('0')
    
    def _generate_amount_reasoning(
        self,
        score: int,
        risk_band: int,
        portfolio_value: Decimal,
        total_debt: Decimal,
        recommended_amount: Decimal,
        max_affordable: Decimal
    ) -> str:
        """Generate human-readable reasoning for amount recommendation"""
        reasons = []
        
        if score >= 800:
            reasons.append("Your excellent credit score")
        elif score >= 600:
            reasons.append("Your good credit score")
        else:
            reasons.append("Your current credit score")
        
        if portfolio_value > 0:
            reasons.append(f"portfolio value of {float(portfolio_value):.2f} QIE")
        
        if total_debt > 0:
            reasons.append(f"existing debt of {float(total_debt):.2f} QIE")
        
        reasons.append(f"recommends a loan amount of {float(recommended_amount):.2f} QIE")
        
        return ", ".join(reasons) + "."
    
    def _generate_terms_reasoning(
        self,
        score: int,
        risk_band: int,
        rate: Decimal,
        term: int
    ) -> str:
        """Generate human-readable reasoning for terms recommendation"""
        risk_descriptions = {1: "low risk", 2: "moderate risk", 3: "higher risk"}
        risk_desc = risk_descriptions.get(risk_band, "moderate risk")
        
        return f"Based on your {risk_desc} profile (score: {score}), recommended terms are {float(rate):.2f}% APR over {term} days."
    
    def _calculate_confidence(
        self,
        score: int,
        portfolio_value: Decimal,
        total_debt: Decimal
    ) -> float:
        """Calculate confidence level (0-1) for recommendation"""
        confidence = 0.5  # Base confidence
        
        # Higher score = higher confidence
        confidence += (score / 1000) * 0.3
        
        # Portfolio value increases confidence
        if portfolio_value > 0:
            confidence += min(0.1, float(portfolio_value) / 100000)  # Up to 0.1 for large portfolio
        
        # Low debt increases confidence
        if portfolio_value > 0:
            debt_ratio = float(total_debt / portfolio_value)
            if debt_ratio < self.SAFE_DEBT_RATIO:
                confidence += 0.1
        
        return min(1.0, max(0.0, confidence))


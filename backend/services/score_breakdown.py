"""
Score breakdown analyzer for detailed score analysis by category
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from utils.logger import get_logger
from services.scoring import ScoringService
from services.portfolio_service import PortfolioService
from services.loan_service import LoanService
from services.staking import StakingService

logger = get_logger(__name__)


class ScoreBreakdownAnalyzer:
    """Service for breaking down scores by category"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.portfolio_service = PortfolioService()
        self.loan_service = LoanService()
        self.staking_service = StakingService()
    
    async def breakdown_score(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Break down score by category
        
        Args:
            address: Wallet address
            
        Returns:
            Score breakdown dict
        """
        try:
            # Get overall score
            score_info = await self.scoring_service.compute_score(address)
            overall_score = score_info.get('score', 0)
            
            # Get category scores
            category_scores = await self.get_category_scores(address)
            
            # Get factor contributions
            factor_contributions = await self.get_factor_contributions(address)
            
            return {
                "address": address,
                "overall_score": overall_score,
                "risk_band": score_info.get('riskBand', 0),
                "category_scores": category_scores,
                "factor_contributions": factor_contributions,
                "breakdown_date": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error breaking down score: {e}", exc_info=True)
            return {
                "address": address,
                "error": str(e),
            }
    
    async def get_category_scores(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Get scores for each category
        
        Args:
            address: Wallet address
            
        Returns:
            Category scores dict
        """
        try:
            categories = {}
            
            # Transaction History Category
            try:
                portfolio_data = await self.portfolio_service.get_transaction_summary(address)
                tx_score = self._calculate_transaction_score(portfolio_data)
                categories['transaction_history'] = {
                    "score": tx_score,
                    "max_score": 300,
                    "percentage": (tx_score / 300) * 100,
                    "factors": {
                        "total_transactions": portfolio_data.get('total_transactions', 0),
                        "total_volume": portfolio_data.get('total_volume', 0),
                        "unique_contracts": portfolio_data.get('unique_contracts', 0),
                        "days_active": portfolio_data.get('days_active', 0),
                    },
                }
            except Exception as e:
                logger.warning(f"Error calculating transaction score: {e}")
                categories['transaction_history'] = {"score": 0, "max_score": 300}
            
            # Portfolio Category
            try:
                portfolio_value = await self.portfolio_service.get_total_portfolio_value(address)
                token_holdings = await self.portfolio_service.get_token_holdings(address)
                portfolio_score = self._calculate_portfolio_score(portfolio_value, len(token_holdings))
                categories['portfolio'] = {
                    "score": portfolio_score,
                    "max_score": 200,
                    "percentage": (portfolio_score / 200) * 100,
                    "factors": {
                        "total_value": portfolio_value,
                        "token_count": len(token_holdings),
                    },
                }
            except Exception as e:
                logger.warning(f"Error calculating portfolio score: {e}")
                categories['portfolio'] = {"score": 0, "max_score": 200}
            
            # Staking Category
            try:
                staking_tier = self.staking_service.get_integration_tier(address)
                staked_amount = self.staking_service.get_staked_amount(address)
                staking_score = self._calculate_staking_score(staking_tier, staked_amount)
                categories['staking'] = {
                    "score": staking_score,
                    "max_score": 150,
                    "percentage": (staking_score / 150) * 100,
                    "factors": {
                        "staking_tier": staking_tier,
                        "staked_amount": staked_amount,
                    },
                }
            except Exception as e:
                logger.warning(f"Error calculating staking score: {e}")
                categories['staking'] = {"score": 0, "max_score": 150}
            
            # Loan Repayment Category
            try:
                loans = await self.loan_service.get_loans_by_user(address)
                repayment_score = self._calculate_repayment_score(loans)
                categories['loan_repayment'] = {
                    "score": repayment_score,
                    "max_score": 200,
                    "percentage": (repayment_score / 200) * 100,
                    "factors": {
                        "total_loans": len(loans),
                        "repaid_loans": len([l for l in loans if l.get('status') == 'repaid']),
                        "active_loans": len([l for l in loans if l.get('status') == 'active']),
                    },
                }
            except Exception as e:
                logger.warning(f"Error calculating repayment score: {e}")
                categories['loan_repayment'] = {"score": 0, "max_score": 200}
            
            # Verification Category (placeholder - would integrate with verification service)
            categories['verification'] = {
                "score": 0,
                "max_score": 150,
                "percentage": 0,
                "factors": {
                    "kyc_verified": False,
                    "humanity_verified": False,
                    "multisig_detected": False,
                },
            }
            
            return categories
        except Exception as e:
            logger.error(f"Error getting category scores: {e}", exc_info=True)
            return {}
    
    async def get_factor_contributions(
        self,
        address: str
    ) -> List[Dict[str, Any]]:
        """
        Get contribution of each factor
        
        Args:
            address: Wallet address
            
        Returns:
            List of factor contribution dicts
        """
        try:
            contributions = []
            
            # Get score info
            score_info = await self.scoring_service.compute_score(address)
            
            # Base score factors
            base_score = score_info.get('baseScore', 0)
            staking_boost = score_info.get('stakingBoost', 0)
            oracle_penalty = score_info.get('oraclePenalty', 0)
            
            contributions.append({
                "factor": "Base Score",
                "contribution": base_score,
                "type": "base",
            })
            
            if staking_boost > 0:
                contributions.append({
                    "factor": "Staking Boost",
                    "contribution": staking_boost,
                    "type": "boost",
                })
            
            if oracle_penalty > 0:
                contributions.append({
                    "factor": "Oracle Penalty",
                    "contribution": -oracle_penalty,
                    "type": "penalty",
                })
            
            return contributions
        except Exception as e:
            logger.error(f"Error getting factor contributions: {e}", exc_info=True)
            return []
    
    async def get_score_trends(
        self,
        address: str,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze score trends
        
        Args:
            address: Wallet address
            timeframe_days: Number of days to analyze
            
        Returns:
            Score trends dict
        """
        try:
            from database.connection import get_session
            from database.models import ScoreHistory
            from sqlalchemy import select, func
            from datetime import datetime, timedelta
            
            async with get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)
                
                result = await session.execute(
                    select(ScoreHistory)
                    .where(
                        ScoreHistory.wallet_address == address,
                        ScoreHistory.computed_at >= cutoff_date
                    )
                    .order_by(ScoreHistory.computed_at.asc())
                )
                history = result.scalars().all()
                
                if len(history) < 2:
                    return {
                        "trend": "insufficient_data",
                        "change": 0,
                        "history_points": len(history),
                    }
                
                first_score = history[0].score
                last_score = history[-1].score
                change = last_score - first_score
                
                # Calculate trend
                if change > 10:
                    trend = "increasing"
                elif change < -10:
                    trend = "decreasing"
                else:
                    trend = "stable"
                
                # Calculate average
                avg_score = sum(h.score for h in history) / len(history)
                
                return {
                    "trend": trend,
                    "change": change,
                    "change_percentage": (change / first_score * 100) if first_score > 0 else 0,
                    "first_score": first_score,
                    "last_score": last_score,
                    "average_score": avg_score,
                    "history_points": len(history),
                    "timeframe_days": timeframe_days,
                }
        except Exception as e:
            logger.error(f"Error getting score trends: {e}", exc_info=True)
            return {
                "trend": "error",
                "error": str(e),
            }
    
    def _calculate_transaction_score(self, portfolio_data: Dict[str, Any]) -> int:
        """Calculate score based on transaction history"""
        tx_count = portfolio_data.get('total_transactions', 0)
        volume = portfolio_data.get('total_volume', 0)
        unique_contracts = portfolio_data.get('unique_contracts', 0)
        days_active = portfolio_data.get('days_active', 0)
        
        score = 0
        
        # Transaction count (max 100 points)
        if tx_count >= 100:
            score += 100
        elif tx_count >= 50:
            score += 75
        elif tx_count >= 20:
            score += 50
        elif tx_count >= 10:
            score += 25
        
        # Volume (max 100 points)
        if volume >= 10000:
            score += 100
        elif volume >= 5000:
            score += 75
        elif volume >= 1000:
            score += 50
        elif volume >= 100:
            score += 25
        
        # Diversity (max 50 points)
        if unique_contracts >= 20:
            score += 50
        elif unique_contracts >= 10:
            score += 30
        elif unique_contracts >= 5:
            score += 15
        
        # Activity duration (max 50 points)
        if days_active >= 180:
            score += 50
        elif days_active >= 90:
            score += 30
        elif days_active >= 30:
            score += 15
        
        return min(score, 300)
    
    def _calculate_portfolio_score(self, portfolio_value: float, token_count: int) -> int:
        """Calculate score based on portfolio"""
        score = 0
        
        # Portfolio value (max 150 points)
        if portfolio_value >= 10000:
            score += 150
        elif portfolio_value >= 5000:
            score += 120
        elif portfolio_value >= 1000:
            score += 90
        elif portfolio_value >= 500:
            score += 60
        elif portfolio_value >= 100:
            score += 30
        
        # Token diversity (max 50 points)
        if token_count >= 10:
            score += 50
        elif token_count >= 5:
            score += 30
        elif token_count >= 2:
            score += 15
        
        return min(score, 200)
    
    def _calculate_staking_score(self, staking_tier: int, staked_amount: float) -> int:
        """Calculate score based on staking"""
        score = 0
        
        # Staking tier (max 100 points)
        if staking_tier >= 3:
            score += 100
        elif staking_tier >= 2:
            score += 75
        elif staking_tier >= 1:
            score += 50
        
        # Staked amount (max 50 points)
        if staked_amount >= 10000:
            score += 50
        elif staked_amount >= 5000:
            score += 40
        elif staked_amount >= 1000:
            score += 30
        elif staked_amount >= 100:
            score += 15
        
        return min(score, 150)
    
    def _calculate_repayment_score(self, loans: List[Dict[str, Any]]) -> int:
        """Calculate score based on loan repayment history"""
        if not loans:
            return 100  # No loans = neutral score
        
        total_loans = len(loans)
        repaid_loans = len([l for l in loans if l.get('status') == 'repaid'])
        active_loans = len([l for l in loans if l.get('status') == 'active'])
        defaulted_loans = len([l for l in loans if l.get('status') == 'defaulted'])
        
        score = 0
        
        # Repayment rate (max 150 points)
        if total_loans > 0:
            repayment_rate = repaid_loans / total_loans
            score += int(repayment_rate * 150)
        
        # Active loans (max 50 points) - having active loans shows trust
        if active_loans > 0:
            score += min(active_loans * 10, 50)
        
        # Penalty for defaults
        if defaulted_loans > 0:
            score -= defaulted_loans * 50
        
        return max(0, min(score, 200))


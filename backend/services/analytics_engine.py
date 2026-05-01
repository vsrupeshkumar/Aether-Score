"""
Analytics engine for comprehensive analytics and insights
"""
from typing import Dict, List, Optional, Any
from utils.logger import get_logger
from services.score_breakdown import ScoreBreakdownAnalyzer
from services.wallet_comparator import WalletComparator
from services.benchmark_service import BenchmarkService
from services.scoring import ScoringService

logger = get_logger(__name__)


class AnalyticsEngine:
    """Service for comprehensive analytics"""
    
    def __init__(self):
        self.score_breakdown = ScoreBreakdownAnalyzer()
        self.wallet_comparator = WalletComparator()
        self.benchmark_service = BenchmarkService()
        self.scoring_service = ScoringService()
    
    async def get_comprehensive_analytics(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Get all analytics
        
        Args:
            address: Wallet address
            
        Returns:
            Comprehensive analytics dict
        """
        try:
            # Get score breakdown
            breakdown = await self.score_breakdown.breakdown_score(address)
            
            # Get similar wallets
            similar_wallets = await self.wallet_comparator.find_similar_wallets(address, limit=5)
            
            # Get comparison metrics
            comparison_metrics = await self.wallet_comparator.get_comparison_metrics(
                address, similar_wallets
            )
            
            # Get percentile rank
            percentile_rank = await self.wallet_comparator.get_percentile_rank(address)
            
            # Get benchmark comparison
            benchmark_comparison = await self.benchmark_service.compare_to_benchmark(address)
            
            # Get score trends
            trends = await self.score_breakdown.get_score_trends(address, timeframe_days=30)
            
            return {
                "address": address,
                "score_breakdown": breakdown,
                "similar_wallets": similar_wallets,
                "comparison_metrics": comparison_metrics,
                "percentile_rank": percentile_rank,
                "benchmark_comparison": benchmark_comparison,
                "score_trends": trends,
                "generated_at": None,  # Will be set by caller
            }
        except Exception as e:
            logger.error(f"Error getting comprehensive analytics: {e}", exc_info=True)
            return {
                "address": address,
                "error": str(e),
            }
    
    async def generate_insights(
        self,
        address: str
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable insights
        
        Args:
            address: Wallet address
            
        Returns:
            List of insight dicts
        """
        try:
            insights = []
            
            # Get score info
            score_info = await self.scoring_service.compute_score(address)
            score = score_info.get('score', 0)
            risk_band = score_info.get('riskBand', 0)
            
            # Get breakdown
            breakdown = await self.score_breakdown.breakdown_score(address)
            category_scores = breakdown.get('category_scores', {})
            
            # Generate insights based on category scores
            for category, data in category_scores.items():
                percentage = data.get('percentage', 0)
                
                if percentage < 50:
                    insights.append({
                        "category": category,
                        "type": "improvement_opportunity",
                        "severity": "medium",
                        "message": f"Your {category.replace('_', ' ')} score is below average ({percentage:.1f}%). Consider improving this area to boost your overall score.",
                        "suggested_actions": self._get_suggested_actions(category),
                    })
                elif percentage < 70:
                    insights.append({
                        "category": category,
                        "type": "optimization",
                        "severity": "low",
                        "message": f"Your {category.replace('_', ' ')} score is moderate ({percentage:.1f}%). There's room for improvement.",
                        "suggested_actions": self._get_suggested_actions(category),
                    })
            
            # Risk band insights
            if risk_band >= 2:
                insights.append({
                    "category": "risk_band",
                    "type": "risk_alert",
                    "severity": "high",
                    "message": f"Your risk band is {risk_band} (Medium/High Risk). Consider improving your credit profile to lower your risk band.",
                    "suggested_actions": [
                        "Increase transaction activity",
                        "Maintain consistent loan repayments",
                        "Consider staking NCRD tokens",
                    ],
                })
            
            # Score trend insights
            trends = await self.score_breakdown.get_score_trends(address, timeframe_days=30)
            if trends.get('trend') == 'decreasing':
                insights.append({
                    "category": "score_trend",
                    "type": "trend_alert",
                    "severity": "medium",
                    "message": f"Your score has decreased by {trends.get('change', 0)} points in the last 30 days. Review recent activity to identify causes.",
                    "suggested_actions": [
                        "Review recent transactions",
                        "Check loan repayment status",
                        "Monitor portfolio performance",
                    ],
                })
            elif trends.get('trend') == 'increasing':
                insights.append({
                    "category": "score_trend",
                    "type": "positive_trend",
                    "severity": "low",
                    "message": f"Great! Your score has increased by {trends.get('change', 0)} points in the last 30 days. Keep up the good work!",
                    "suggested_actions": [],
                })
            
            return insights
        except Exception as e:
            logger.error(f"Error generating insights: {e}", exc_info=True)
            return []
    
    async def get_recommendations(
        self,
        address: str
    ) -> List[Dict[str, Any]]:
        """
        Get improvement recommendations
        
        Args:
            address: Wallet address
            
        Returns:
            List of recommendation dicts
        """
        try:
            recommendations = []
            
            # Get breakdown
            breakdown = await self.score_breakdown.breakdown_score(address)
            category_scores = breakdown.get('category_scores', {})
            
            # Generate recommendations for each category
            for category, data in category_scores.items():
                percentage = data.get('percentage', 0)
                
                if percentage < 60:
                    rec = {
                        "category": category,
                        "priority": "high" if percentage < 40 else "medium",
                        "current_score": data.get('score', 0),
                        "max_score": data.get('max_score', 0),
                        "recommendations": self._get_category_recommendations(category, data),
                    }
                    recommendations.append(rec)
            
            # Sort by priority
            priority_order = {"high": 0, "medium": 1, "low": 2}
            recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}", exc_info=True)
            return []
    
    def _get_suggested_actions(self, category: str) -> List[str]:
        """Get suggested actions for category"""
        actions_map = {
            'transaction_history': [
                "Increase transaction frequency",
                "Diversify transaction types",
                "Interact with more DeFi protocols",
            ],
            'portfolio': [
                "Increase portfolio value",
                "Diversify token holdings",
                "Maintain consistent portfolio balance",
            ],
            'staking': [
                "Stake NCRD tokens",
                "Increase staking amount",
                "Maintain staking position",
            ],
            'loan_repayment': [
                "Make timely loan repayments",
                "Consider repaying loans early",
                "Maintain good repayment history",
            ],
            'verification': [
                "Complete KYC verification",
                "Verify proof of humanity",
                "Use multi-sig wallet",
            ],
        }
        return actions_map.get(category, ["Review and improve this category"])
    
    def _get_category_recommendations(
        self,
        category: str,
        category_data: Dict[str, Any]
    ) -> List[str]:
        """Get specific recommendations for category"""
        factors = category_data.get('factors', {})
        recommendations = []
        
        if category == 'transaction_history':
            tx_count = factors.get('total_transactions', 0)
            if tx_count < 20:
                recommendations.append(f"Increase transaction count (currently {tx_count}, target: 50+)")
            
            unique_contracts = factors.get('unique_contracts', 0)
            if unique_contracts < 5:
                recommendations.append(f"Diversify interactions (currently {unique_contracts} contracts, target: 10+)")
        
        elif category == 'portfolio':
            portfolio_value = factors.get('total_value', 0)
            if portfolio_value < 1000:
                recommendations.append(f"Increase portfolio value (currently {portfolio_value:.2f}, target: 5000+)")
        
        elif category == 'staking':
            staking_tier = factors.get('staking_tier', 0)
            if staking_tier < 2:
                recommendations.append("Upgrade staking tier to Silver or Gold")
        
        elif category == 'loan_repayment':
            repaid_loans = factors.get('repaid_loans', 0)
            total_loans = factors.get('total_loans', 0)
            if total_loans > 0 and repaid_loans / total_loans < 0.8:
                recommendations.append("Improve loan repayment rate (target: 80%+)")
        
        return recommendations if recommendations else self._get_suggested_actions(category)


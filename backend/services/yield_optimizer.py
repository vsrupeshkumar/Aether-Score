"""
Yield optimizer service for yield strategy analysis and suggestions
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class YieldOptimizer:
    """Service for analyzing portfolios and suggesting yield optimization strategies"""
    
    async def analyze_portfolio(
        self,
        address: str,
        session=None
    ) -> Dict[str, Any]:
        """
        Analyze user portfolio for yield opportunities
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Portfolio analysis dict
        """
        try:
            from database.connection import get_session
            from database.models import YieldStrategy
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._analyze_portfolio(address, db_session)
            else:
                return await self._analyze_portfolio(address, session)
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}", exc_info=True)
            return {}
    
    async def _analyze_portfolio(
        self,
        address: str,
        session
    ) -> Dict[str, Any]:
        """Analyze portfolio from database"""
        from database.models import YieldStrategy
        from sqlalchemy import select
        
        try:
            # Get user's yield strategies
            result = await session.execute(
                select(YieldStrategy).where(YieldStrategy.wallet_address == address)
            )
            strategies = result.scalars().all()
            
            total_amount = sum(Decimal(str(s.amount)) for s in strategies)
            total_rewards = sum(Decimal(str(s.total_rewards)) for s in strategies)
            
            # Calculate weighted average APY
            weighted_apy = Decimal('0')
            if total_amount > 0:
                for s in strategies:
                    if s.apy:
                        weight = Decimal(str(s.amount)) / total_amount
                        weighted_apy += Decimal(str(s.apy)) * weight
            
            return {
                "wallet_address": address,
                "total_strategies": len(strategies),
                "total_amount": float(total_amount),
                "total_rewards": float(total_rewards),
                "weighted_avg_apy": float(weighted_apy),
                "strategies": [
                    {
                        "id": s.id,
                        "strategy_type": s.strategy_type,
                        "protocol": s.protocol,
                        "token_address": s.token_address,
                        "amount": float(s.amount),
                        "apy": float(s.apy) if s.apy else None,
                        "auto_compound_enabled": s.auto_compound_enabled,
                    }
                    for s in strategies
                ],
            }
        except Exception as e:
            logger.error(f"Error in _analyze_portfolio: {e}", exc_info=True)
            return {}
    
    async def suggest_strategies(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Suggest yield optimization strategies
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of strategy suggestions
        """
        try:
            portfolio = await self.analyze_portfolio(address, session)
            
            suggestions = []
            
            # Suggest staking if not already staking
            has_staking = any(
                s['strategy_type'] == 'staking'
                for s in portfolio.get('strategies', [])
            )
            
            if not has_staking:
                suggestions.append({
                    "strategy_type": "staking",
                    "protocol": "AETHER-SCORE Staking",
                    "recommendation": "Consider staking NCRD tokens to boost your credit score",
                    "potential_apy": 10.0,  # Example APY
                    "score_boost": "Up to 300 points",
                })
            
            # Suggest auto-compound if not enabled
            strategies_without_compound = [
                s for s in portfolio.get('strategies', [])
                if not s.get('auto_compound_enabled', False)
            ]
            
            if strategies_without_compound:
                suggestions.append({
                    "strategy_type": "auto_compound",
                    "recommendation": f"Enable auto-compounding for {len(strategies_without_compound)} strategy(ies) to maximize returns",
                    "potential_boost": "10-20% additional yield",
                })
            
            # Suggest yield farming if available
            suggestions.append({
                "strategy_type": "yield_farming",
                "protocol": "QIE Yield Protocol",
                "recommendation": "Explore yield farming opportunities for higher APY",
                "potential_apy": 15.0,  # Example APY
            })
            
            return suggestions
        except Exception as e:
            logger.error(f"Error suggesting strategies: {e}", exc_info=True)
            return []
    
    async def calculate_optimal_staking(
        self,
        address: str,
        target_score_boost: Optional[int] = None,
        session=None
    ) -> Dict[str, Any]:
        """
        Calculate optimal staking amount for score boost
        
        Args:
            address: Wallet address
            target_score_boost: Target score boost (optional)
            session: Database session (optional)
            
        Returns:
            Optimal staking recommendation dict
        """
        try:
            # Simplified calculation
            # In production, would use actual staking tiers and boost calculations
            
            if target_score_boost is None:
                target_score_boost = 100  # Default target
            
            # Assume linear relationship: 1000 tokens = 100 points boost
            tokens_per_point = Decimal('10')
            optimal_amount = Decimal(str(target_score_boost)) * tokens_per_point
            
            return {
                "wallet_address": address,
                "target_score_boost": target_score_boost,
                "recommended_staking_amount": float(optimal_amount),
                "estimated_apy": 10.0,
                "estimated_monthly_rewards": float(optimal_amount * Decimal('0.1') / Decimal('12')),
                "explanation": f"Staking {optimal_amount} tokens should provide approximately {target_score_boost} points boost",
            }
        except Exception as e:
            logger.error(f"Error calculating optimal staking: {e}", exc_info=True)
            return {}
    
    async def compare_yield_options(
        self,
        token_address: str,
        amount: Decimal,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Compare yield options for a token
        
        Args:
            token_address: Token address
            amount: Amount to compare
            session: Database session (optional)
            
        Returns:
            List of yield option comparisons
        """
        try:
            # Simplified comparison
            # In production, would fetch real APY from multiple protocols
            
            options = [
                {
                    "protocol": "AETHER-SCORE Staking",
                    "strategy_type": "staking",
                    "apy": 10.0,
                    "estimated_annual_yield": float(amount * Decimal('0.1')),
                    "score_boost": "Yes (up to 300 points)",
                    "risk": "Low",
                },
                {
                    "protocol": "QIE Yield Protocol",
                    "strategy_type": "yield_farming",
                    "apy": 15.0,
                    "estimated_annual_yield": float(amount * Decimal('0.15')),
                    "score_boost": "No",
                    "risk": "Medium",
                },
                {
                    "protocol": "Liquidity Pool",
                    "strategy_type": "yield_farming",
                    "apy": 20.0,
                    "estimated_annual_yield": float(amount * Decimal('0.2')),
                    "score_boost": "No",
                    "risk": "High",
                },
            ]
            
            # Sort by APY (descending)
            options.sort(key=lambda x: x['apy'], reverse=True)
            
            return options
        except Exception as e:
            logger.error(f"Error comparing yield options: {e}", exc_info=True)
            return []
    
    async def get_available_protocols(self) -> List[Dict[str, Any]]:
        """
        Get list of integrated yield protocols
        
        Returns:
            List of protocol dicts
        """
        try:
            return [
                {
                    "id": "AETHER-SCORE_staking",
                    "name": "AETHER-SCORE Staking",
                    "type": "staking",
                    "supported_tokens": ["NCRD"],
                    "min_amount": 0,
                    "apy_range": "8-12%",
                    "features": ["score_boost", "auto_compound"],
                },
                {
                    "id": "qie_yield",
                    "name": "QIE Yield Protocol",
                    "type": "yield_farming",
                    "supported_tokens": ["QIE", "USDT", "USDC"],
                    "min_amount": 100,
                    "apy_range": "12-18%",
                    "features": ["auto_compound"],
                },
                {
                    "id": "liquidity_pools",
                    "name": "Liquidity Pools",
                    "type": "yield_farming",
                    "supported_tokens": ["QIE", "USDT", "USDC"],
                    "min_amount": 500,
                    "apy_range": "15-25%",
                    "features": ["lp_tokens"],
                },
            ]
        except Exception as e:
            logger.error(f"Error getting available protocols: {e}", exc_info=True)
            return []



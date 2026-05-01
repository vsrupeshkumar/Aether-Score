"""
Collateral rebalancer service for automatic collateral rebalancing
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from services.collateral_manager import CollateralManager

logger = get_logger(__name__)


class CollateralRebalancer:
    """Service for automatic collateral rebalancing"""
    
    # Rebalancing strategies
    STRATEGY_DIVERSIFICATION = 'diversification'
    STRATEGY_VOLATILITY_REDUCTION = 'volatility_reduction'
    STRATEGY_YIELD_OPTIMIZATION = 'yield_optimization'
    
    def __init__(self):
        self.collateral_manager = CollateralManager()
    
    async def check_rebalance_opportunities(
        self,
        loan_id: int,
        session=None
    ) -> bool:
        """
        Check if rebalancing is needed
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            True if rebalancing opportunities exist
        """
        try:
            positions = await self.collateral_manager.get_collateral_positions(loan_id, session)
            
            if len(positions) < 2:
                return False  # Need at least 2 positions to rebalance
            
            # Check if positions are imbalanced (one > 80% of total)
            total_value = sum(Decimal(str(pos['value_usd'])) for pos in positions)
            if total_value == 0:
                return False
            
            for pos in positions:
                percentage = Decimal(str(pos['value_usd'])) / total_value
                if percentage > Decimal('0.8'):
                    return True  # Too concentrated in one token
            
            return False
        except Exception as e:
            logger.error(f"Error checking rebalance opportunities: {e}", exc_info=True)
            return False
    
    async def calculate_optimal_allocation(
        self,
        loan_id: int,
        strategy: str = STRATEGY_DIVERSIFICATION,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate optimal token allocation
        
        Args:
            loan_id: Loan ID
            strategy: Rebalancing strategy
            session: Database session (optional)
            
        Returns:
            Optimal allocation dict
        """
        try:
            positions = await self.collateral_manager.get_collateral_positions(loan_id, session)
            
            if not positions:
                return None
            
            total_value = sum(Decimal(str(pos['value_usd'])) for pos in positions)
            if total_value == 0:
                return None
            
            if strategy == self.STRATEGY_DIVERSIFICATION:
                return await self._calculate_diversification_allocation(positions, total_value)
            elif strategy == self.STRATEGY_VOLATILITY_REDUCTION:
                return await self._calculate_volatility_reduction_allocation(positions, total_value)
            elif strategy == self.STRATEGY_YIELD_OPTIMIZATION:
                return await self._calculate_yield_optimization_allocation(positions, total_value)
            else:
                return await self._calculate_diversification_allocation(positions, total_value)
        except Exception as e:
            logger.error(f"Error calculating optimal allocation: {e}", exc_info=True)
            return None
    
    async def _calculate_diversification_allocation(
        self,
        positions: List[Dict[str, Any]],
        total_value: Decimal
    ) -> Dict[str, Any]:
        """Calculate equal-weight diversification allocation"""
        try:
            num_positions = len(positions)
            target_percentage = Decimal('1') / Decimal(str(num_positions))
            
            allocation = {}
            for pos in positions:
                token_address = pos['token_address']
                current_value = Decimal(str(pos['value_usd']))
                target_value = total_value * target_percentage
                
                allocation[token_address] = {
                    "current_value": float(current_value),
                    "target_value": float(target_value),
                    "difference": float(target_value - current_value),
                    "current_percentage": float(current_value / total_value),
                    "target_percentage": float(target_percentage),
                }
            
            return {
                "strategy": self.STRATEGY_DIVERSIFICATION,
                "total_value": float(total_value),
                "allocation": allocation,
            }
        except Exception as e:
            logger.error(f"Error calculating diversification allocation: {e}", exc_info=True)
            return {}
    
    async def _calculate_volatility_reduction_allocation(
        self,
        positions: List[Dict[str, Any]],
        total_value: Decimal
    ) -> Dict[str, Any]:
        """Calculate allocation favoring stablecoins"""
        try:
            # Simplified: assume native token (0x0) is most stable
            # In production, would check token volatility from oracle
            stable_token = "0x0000000000000000000000000000000000000000"
            
            allocation = {}
            stable_value = Decimal('0')
            
            for pos in positions:
                token_address = pos['token_address']
                current_value = Decimal(str(pos['value_usd']))
                
                if token_address.lower() == stable_token.lower():
                    stable_value = current_value
            
            # Target: 70% in stable token
            target_stable_value = total_value * Decimal('0.7')
            remaining_value = total_value - target_stable_value
            
            num_other = len([p for p in positions if p['token_address'].lower() != stable_token.lower()])
            other_target = remaining_value / Decimal(str(num_other)) if num_other > 0 else Decimal('0')
            
            for pos in positions:
                token_address = pos['token_address']
                current_value = Decimal(str(pos['value_usd']))
                
                if token_address.lower() == stable_token.lower():
                    target_value = target_stable_value
                else:
                    target_value = other_target
                
                allocation[token_address] = {
                    "current_value": float(current_value),
                    "target_value": float(target_value),
                    "difference": float(target_value - current_value),
                }
            
            return {
                "strategy": self.STRATEGY_VOLATILITY_REDUCTION,
                "total_value": float(total_value),
                "allocation": allocation,
            }
        except Exception as e:
            logger.error(f"Error calculating volatility reduction allocation: {e}", exc_info=True)
            return {}
    
    async def _calculate_yield_optimization_allocation(
        self,
        positions: List[Dict[str, Any]],
        total_value: Decimal
    ) -> Dict[str, Any]:
        """Calculate allocation favoring higher-yield tokens"""
        try:
            # Simplified: assume all tokens have same yield
            # In production, would fetch yield rates from protocols
            num_positions = len(positions)
            target_percentage = Decimal('1') / Decimal(str(num_positions))
            
            allocation = {}
            for pos in positions:
                token_address = pos['token_address']
                current_value = Decimal(str(pos['value_usd']))
                target_value = total_value * target_percentage
                
                allocation[token_address] = {
                    "current_value": float(current_value),
                    "target_value": float(target_value),
                    "difference": float(target_value - current_value),
                }
            
            return {
                "strategy": self.STRATEGY_YIELD_OPTIMIZATION,
                "total_value": float(total_value),
                "allocation": allocation,
            }
        except Exception as e:
            logger.error(f"Error calculating yield optimization allocation: {e}", exc_info=True)
            return {}
    
    async def execute_rebalance(
        self,
        loan_id: int,
        strategy: str = STRATEGY_DIVERSIFICATION,
        session=None
    ) -> bool:
        """
        Execute rebalancing
        
        Args:
            loan_id: Loan ID
            strategy: Rebalancing strategy
            session: Database session (optional)
            
        Returns:
            True if rebalanced successfully
        """
        try:
            from database.connection import get_session
            from database.models import RebalanceHistory
            from datetime import datetime
            
            if session is None:
                async with get_session() as db_session:
                    return await self._execute_rebalance(loan_id, strategy, db_session)
            else:
                return await self._execute_rebalance(loan_id, strategy, session)
        except Exception as e:
            logger.error(f"Error executing rebalance: {e}", exc_info=True)
            return False
    
    async def _execute_rebalance(
        self,
        loan_id: int,
        strategy: str,
        session
    ) -> bool:
        """Execute rebalance in database"""
        from database.models import RebalanceHistory
        from datetime import datetime
        
        try:
            # Calculate optimal allocation
            allocation = await self.calculate_optimal_allocation(loan_id, strategy, session)
            
            if not allocation or 'allocation' not in allocation:
                return False
            
            # Execute rebalancing (simplified - would involve actual token swaps in production)
            for token_address, target in allocation['allocation'].items():
                difference = Decimal(str(target['difference']))
                
                if abs(difference) > Decimal('0.01'):  # Only rebalance if significant difference
                    if difference > 0:
                        # Need to add collateral
                        await self.collateral_manager.add_collateral(
                            loan_id, token_address, difference, session
                        )
                    else:
                        # Need to remove collateral
                        await self.collateral_manager.remove_collateral(
                            loan_id, token_address, abs(difference), session
                        )
                    
                    # Record rebalance
                    rebalance = RebalanceHistory(
                        loan_id=loan_id,
                        rebalance_type='auto',
                        from_token=token_address if difference < 0 else '',
                        to_token=token_address if difference > 0 else '',
                        from_amount=abs(difference) if difference < 0 else Decimal('0'),
                        to_amount=difference if difference > 0 else Decimal('0'),
                        reason=f"Auto-rebalance using {strategy} strategy"
                    )
                    session.add(rebalance)
            
            await session.commit()
            logger.info(f"Executed rebalance for loan {loan_id} using {strategy}")
            return True
        except Exception as e:
            logger.error(f"Error in _execute_rebalance: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def get_rebalance_suggestions(
        self,
        loan_id: int,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get rebalancing suggestions
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            List of rebalancing suggestions
        """
        try:
            suggestions = []
            
            # Check each strategy
            for strategy in [
                self.STRATEGY_DIVERSIFICATION,
                self.STRATEGY_VOLATILITY_REDUCTION,
                self.STRATEGY_YIELD_OPTIMIZATION
            ]:
                allocation = await self.calculate_optimal_allocation(loan_id, strategy, session)
                
                if allocation:
                    # Calculate rebalance score (how much improvement)
                    total_difference = sum(
                        abs(Decimal(str(target['difference'])))
                        for target in allocation.get('allocation', {}).values()
                    )
                    
                    if total_difference > Decimal('0.01'):  # Only suggest if meaningful
                        suggestions.append({
                            "strategy": strategy,
                            "allocation": allocation,
                            "rebalance_score": float(total_difference),
                            "recommended": strategy == self.STRATEGY_DIVERSIFICATION,  # Default recommendation
                        })
            
            # Sort by rebalance score (descending)
            suggestions.sort(key=lambda x: x['rebalance_score'], reverse=True)
            
            return suggestions
        except Exception as e:
            logger.error(f"Error getting rebalance suggestions: {e}", exc_info=True)
            return []


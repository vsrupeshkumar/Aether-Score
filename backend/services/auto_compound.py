"""
Auto-compound service for automatic reward compounding
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class AutoCompoundService:
    """Service for managing automatic reward compounding"""
    
    # Minimum compound frequency (hours)
    MIN_COMPOUND_FREQUENCY_HOURS = 24
    
    # Gas cost estimate (in token units)
    ESTIMATED_GAS_COST = Decimal('0.001')
    
    async def enable_auto_compound(
        self,
        address: str,
        strategy_id: int,
        session=None
    ) -> bool:
        """
        Enable auto-compounding for a strategy
        
        Args:
            address: Wallet address
            strategy_id: Strategy ID
            session: Database session (optional)
            
        Returns:
            True if enabled successfully
        """
        try:
            from database.connection import get_session
            from database.models import YieldStrategy
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._enable_auto_compound(address, strategy_id, db_session)
            else:
                return await self._enable_auto_compound(address, strategy_id, session)
        except Exception as e:
            logger.error(f"Error enabling auto-compound: {e}", exc_info=True)
            return False
    
    async def _enable_auto_compound(
        self,
        address: str,
        strategy_id: int,
        session
    ) -> bool:
        """Enable auto-compound in database"""
        from database.models import YieldStrategy
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(YieldStrategy).where(
                    YieldStrategy.id == strategy_id,
                    YieldStrategy.wallet_address == address
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                logger.warning(f"Strategy not found: {strategy_id}")
                return False
            
            strategy.auto_compound_enabled = True
            strategy.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Enabled auto-compound for strategy {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"Error in _enable_auto_compound: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def disable_auto_compound(
        self,
        address: str,
        strategy_id: int,
        session=None
    ) -> bool:
        """
        Disable auto-compounding for a strategy
        
        Args:
            address: Wallet address
            strategy_id: Strategy ID
            session: Database session (optional)
            
        Returns:
            True if disabled successfully
        """
        try:
            from database.connection import get_session
            from database.models import YieldStrategy
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._disable_auto_compound(address, strategy_id, db_session)
            else:
                return await self._disable_auto_compound(address, strategy_id, session)
        except Exception as e:
            logger.error(f"Error disabling auto-compound: {e}", exc_info=True)
            return False
    
    async def _disable_auto_compound(
        self,
        address: str,
        strategy_id: int,
        session
    ) -> bool:
        """Disable auto-compound in database"""
        from database.models import YieldStrategy
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(YieldStrategy).where(
                    YieldStrategy.id == strategy_id,
                    YieldStrategy.wallet_address == address
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return False
            
            strategy.auto_compound_enabled = False
            strategy.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Disabled auto-compound for strategy {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"Error in _disable_auto_compound: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def compound_rewards(
        self,
        strategy_id: int,
        session=None
    ) -> bool:
        """
        Execute compounding for a strategy
        
        Args:
            strategy_id: Strategy ID
            session: Database session (optional)
            
        Returns:
            True if compounded successfully
        """
        try:
            from database.connection import get_session
            from database.models import YieldStrategy
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._compound_rewards(strategy_id, db_session)
            else:
                return await self._compound_rewards(strategy_id, session)
        except Exception as e:
            logger.error(f"Error compounding rewards: {e}", exc_info=True)
            return False
    
    async def _compound_rewards(
        self,
        strategy_id: int,
        session
    ) -> bool:
        """Compound rewards in database"""
        from database.models import YieldStrategy
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(YieldStrategy).where(YieldStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return False
            
            # Calculate rewards since last compound
            if strategy.last_compounded_at:
                time_since = datetime.utcnow() - strategy.last_compounded_at
                hours = time_since.total_seconds() / 3600
            else:
                hours = 24  # Default to 24 hours
            
            # Calculate rewards (simplified)
            if strategy.apy:
                apy_decimal = Decimal(str(strategy.apy))
                principal = Decimal(str(strategy.amount))
                rewards = principal * (apy_decimal / Decimal('100')) * (Decimal(str(hours)) / Decimal('8760'))
            else:
                rewards = Decimal('0')
            
            # Add rewards to principal
            strategy.amount += rewards
            strategy.total_rewards += rewards
            strategy.last_compounded_at = datetime.utcnow()
            strategy.updated_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Compounded {rewards} rewards for strategy {strategy_id}")
            return True
        except Exception as e:
            logger.error(f"Error in _compound_rewards: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def calculate_compound_frequency(
        self,
        strategy_id: int,
        session=None
    ) -> Dict[str, Any]:
        """
        Calculate optimal compounding frequency
        
        Args:
            strategy_id: Strategy ID
            session: Database session (optional)
            
        Returns:
            Frequency recommendation dict
        """
        try:
            from database.connection import get_session
            from database.models import YieldStrategy
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_compound_frequency(strategy_id, db_session)
            else:
                return await self._calculate_compound_frequency(strategy_id, session)
        except Exception as e:
            logger.error(f"Error calculating compound frequency: {e}", exc_info=True)
            return {}
    
    async def _calculate_compound_frequency(
        self,
        strategy_id: int,
        session
    ) -> Dict[str, Any]:
        """Calculate optimal frequency from database"""
        from database.models import YieldStrategy
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(YieldStrategy).where(YieldStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy or not strategy.apy:
                return {
                    "strategy_id": strategy_id,
                    "recommended_frequency_hours": 24,
                    "explanation": "Default frequency",
                }
            
            # Calculate optimal frequency based on APY and gas costs
            # Higher APY = more frequent compounding beneficial
            apy = Decimal(str(strategy.apy))
            amount = Decimal(str(strategy.amount))
            
            # Simplified calculation: compound when rewards > gas cost * 2
            # More sophisticated: use compound interest formula
            if apy > 0 and amount > 0:
                # Calculate daily rewards
                daily_rewards = amount * (apy / Decimal('100')) / Decimal('365')
                
                # Find frequency where rewards > gas cost
                # For simplicity, use 24 hours for high APY, 48-72 for lower
                if apy >= 15:
                    frequency_hours = 24
                elif apy >= 10:
                    frequency_hours = 48
                else:
                    frequency_hours = 72
            else:
                frequency_hours = 24
            
            return {
                "strategy_id": strategy_id,
                "recommended_frequency_hours": frequency_hours,
                "current_apy": float(apy),
                "estimated_daily_rewards": float(daily_rewards) if apy > 0 and amount > 0 else 0,
                "explanation": f"Recommended compounding every {frequency_hours} hours based on APY and gas costs",
            }
        except Exception as e:
            logger.error(f"Error in _calculate_compound_frequency: {e}", exc_info=True)
            return {}
    
    async def get_compound_history(
        self,
        address: str,
        limit: int = 50,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get compounding history for a user
        
        Args:
            address: Wallet address
            limit: Maximum number of records
            session: Database session (optional)
            
        Returns:
            List of compound history dicts
        """
        try:
            from database.connection import get_session
            from database.models import YieldStrategy
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_compound_history(address, limit, db_session)
            else:
                return await self._get_compound_history(address, limit, session)
        except Exception as e:
            logger.error(f"Error getting compound history: {e}", exc_info=True)
            return []
    
    async def _get_compound_history(
        self,
        address: str,
        limit: int,
        session
    ) -> List[Dict[str, Any]]:
        """Get compound history from database"""
        from database.models import YieldStrategy
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(YieldStrategy).where(
                    YieldStrategy.wallet_address == address,
                    YieldStrategy.auto_compound_enabled == True
                ).order_by(YieldStrategy.last_compounded_at.desc()).limit(limit)
            )
            strategies = result.scalars().all()
            
            history = []
            for strategy in strategies:
                if strategy.last_compounded_at:
                    history.append({
                        "strategy_id": strategy.id,
                        "strategy_type": strategy.strategy_type,
                        "protocol": strategy.protocol,
                        "last_compounded_at": strategy.last_compounded_at.isoformat(),
                        "total_rewards": float(strategy.total_rewards),
                        "current_amount": float(strategy.amount),
                    })
            
            return history
        except Exception as e:
            logger.error(f"Error in _get_compound_history: {e}", exc_info=True)
            return []


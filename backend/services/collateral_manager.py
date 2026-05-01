"""
Collateral manager service for multi-asset collateral management
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class CollateralManager:
    """Service for managing multi-asset collateral positions"""
    
    # Default accepted tokens (ERC-20 addresses)
    DEFAULT_ACCEPTED_TOKENS = [
        "0x0000000000000000000000000000000000000000",  # Native token (QIE)
        # Add more token addresses as needed
    ]
    
    async def add_collateral(
        self,
        loan_id: int,
        token_address: str,
        amount: Decimal,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Add collateral to a loan
        
        Args:
            loan_id: Loan ID
            token_address: Token address
            amount: Collateral amount
            session: Database session (optional)
            
        Returns:
            Created collateral position dict
        """
        try:
            from database.connection import get_session
            from database.models import CollateralPosition, Loan
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._add_collateral(loan_id, token_address, amount, db_session)
            else:
                return await self._add_collateral(loan_id, token_address, amount, session)
        except Exception as e:
            logger.error(f"Error adding collateral: {e}", exc_info=True)
            return None
    
    async def _add_collateral(
        self,
        loan_id: int,
        token_address: str,
        amount: Decimal,
        session
    ) -> Optional[Dict[str, Any]]:
        """Add collateral in database"""
        from database.models import CollateralPosition, Loan
        from sqlalchemy import select
        
        try:
            # Get loan
            loan_result = await session.execute(
                select(Loan).where(Loan.id == loan_id)
            )
            loan = loan_result.scalar_one_or_none()
            
            if not loan:
                logger.warning(f"Loan not found: {loan_id}")
                return None
            
            # Calculate USD value (simplified - would use oracle in production)
            value_usd = await self._calculate_token_value(token_address, amount)
            
            # Check if position already exists
            position_result = await session.execute(
                select(CollateralPosition).where(
                    CollateralPosition.loan_id == loan_id,
                    CollateralPosition.token_address == token_address
                )
            )
            position = position_result.scalar_one_or_none()
            
            if position:
                # Update existing position
                position.amount += amount
                position.value_usd += value_usd
            else:
                # Create new position
                position = CollateralPosition(
                    loan_id=loan_id,
                    wallet_address=loan.borrower_address,
                    token_address=token_address,
                    amount=amount,
                    value_usd=value_usd
                )
                session.add(position)
            
            await session.commit()
            
            # Update LTV and health
            await self._update_position_metrics(loan_id, session)
            
            logger.info(f"Added collateral {amount} {token_address} to loan {loan_id}")
            
            return {
                "id": position.id,
                "loan_id": loan_id,
                "token_address": token_address,
                "amount": float(position.amount),
                "value_usd": float(position.value_usd),
            }
        except Exception as e:
            logger.error(f"Error in _add_collateral: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def remove_collateral(
        self,
        loan_id: int,
        token_address: str,
        amount: Decimal,
        session=None
    ) -> bool:
        """
        Remove collateral from a loan
        
        Args:
            loan_id: Loan ID
            token_address: Token address
            amount: Amount to remove
            session: Database session (optional)
            
        Returns:
            True if removed successfully
        """
        try:
            from database.connection import get_session
            from database.models import CollateralPosition
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._remove_collateral(loan_id, token_address, amount, db_session)
            else:
                return await self._remove_collateral(loan_id, token_address, amount, session)
        except Exception as e:
            logger.error(f"Error removing collateral: {e}", exc_info=True)
            return False
    
    async def _remove_collateral(
        self,
        loan_id: int,
        token_address: str,
        amount: Decimal,
        session
    ) -> bool:
        """Remove collateral in database"""
        from database.models import CollateralPosition
        from sqlalchemy import select
        
        try:
            # Get position
            position_result = await session.execute(
                select(CollateralPosition).where(
                    CollateralPosition.loan_id == loan_id,
                    CollateralPosition.token_address == token_address
                )
            )
            position = position_result.scalar_one_or_none()
            
            if not position:
                logger.warning(f"Collateral position not found: {loan_id}, {token_address}")
                return False
            
            if position.amount < amount:
                logger.warning(f"Insufficient collateral: {loan_id}, {token_address}")
                return False
            
            # Update amount
            value_usd = await self._calculate_token_value(token_address, amount)
            position.amount -= amount
            position.value_usd -= value_usd
            
            # Delete if zero
            if position.amount <= 0:
                await session.delete(position)
            
            await session.commit()
            
            # Update LTV and health
            await self._update_position_metrics(loan_id, session)
            
            logger.info(f"Removed collateral {amount} {token_address} from loan {loan_id}")
            return True
        except Exception as e:
            logger.error(f"Error in _remove_collateral: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def get_collateral_positions(
        self,
        loan_id: int,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get all collateral positions for a loan
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            List of collateral position dicts
        """
        try:
            from database.connection import get_session
            from database.models import CollateralPosition
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_positions(loan_id, db_session)
            else:
                return await self._get_positions(loan_id, session)
        except Exception as e:
            logger.error(f"Error getting collateral positions: {e}", exc_info=True)
            return []
    
    async def _get_positions(
        self,
        loan_id: int,
        session
    ) -> List[Dict[str, Any]]:
        """Get positions from database"""
        from database.models import CollateralPosition
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(CollateralPosition).where(CollateralPosition.loan_id == loan_id)
            )
            positions = result.scalars().all()
            
            return [
                {
                    "id": pos.id,
                    "loan_id": pos.loan_id,
                    "token_address": pos.token_address,
                    "amount": float(pos.amount),
                    "value_usd": float(pos.value_usd),
                    "ltv_ratio": float(pos.ltv_ratio) if pos.ltv_ratio else None,
                    "health_ratio": float(pos.health_ratio) if pos.health_ratio else None,
                    "last_updated": pos.last_updated.isoformat() if pos.last_updated else None,
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error in _get_positions: {e}", exc_info=True)
            return []
    
    async def calculate_total_collateral_value(
        self,
        loan_id: int,
        session=None
    ) -> Decimal:
        """
        Calculate total USD value of all collateral
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            Total collateral value in USD
        """
        try:
            positions = await self.get_collateral_positions(loan_id, session)
            total = sum(Decimal(str(pos['value_usd'])) for pos in positions)
            return total
        except Exception as e:
            logger.error(f"Error calculating total collateral value: {e}", exc_info=True)
            return Decimal('0')
    
    async def calculate_ltv(
        self,
        loan_id: int,
        session=None
    ) -> Optional[float]:
        """
        Calculate loan-to-value ratio
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            LTV ratio (0-1) or None
        """
        try:
            from database.connection import get_session
            from database.models import Loan
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_ltv(loan_id, db_session)
            else:
                return await self._calculate_ltv(loan_id, session)
        except Exception as e:
            logger.error(f"Error calculating LTV: {e}", exc_info=True)
            return None
    
    async def _calculate_ltv(
        self,
        loan_id: int,
        session
    ) -> Optional[float]:
        """Calculate LTV from database"""
        from database.models import Loan
        from sqlalchemy import select
        
        try:
            # Get loan
            loan_result = await session.execute(
                select(Loan).where(Loan.id == loan_id)
            )
            loan = loan_result.scalar_one_or_none()
            
            if not loan:
                return None
            
            loan_amount = Decimal(str(loan.principal_amount))
            collateral_value = await self.calculate_total_collateral_value(loan_id, session)
            
            if collateral_value == 0:
                return None
            
            ltv = float(loan_amount / collateral_value)
            return ltv
        except Exception as e:
            logger.error(f"Error in _calculate_ltv: {e}", exc_info=True)
            return None
    
    async def get_accepted_tokens(self) -> List[str]:
        """
        Get whitelist of accepted collateral tokens
        
        Returns:
            List of token addresses
        """
        try:
            # In production, this would be fetched from database or config
            return self.DEFAULT_ACCEPTED_TOKENS.copy()
        except Exception as e:
            logger.error(f"Error getting accepted tokens: {e}", exc_info=True)
            return []
    
    async def _calculate_token_value(
        self,
        token_address: str,
        amount: Decimal
    ) -> Decimal:
        """
        Calculate USD value of tokens (simplified)
        
        Args:
            token_address: Token address
            amount: Token amount
            
        Returns:
            USD value
        """
        try:
            # Simplified: assume 1 token = 1 USD
            # In production, would use price oracle
            return amount
        except Exception as e:
            logger.error(f"Error calculating token value: {e}", exc_info=True)
            return Decimal('0')
    
    async def _update_position_metrics(
        self,
        loan_id: int,
        session
    ) -> None:
        """Update LTV and health ratios for all positions"""
        from database.models import CollateralPosition
        from sqlalchemy import select
        
        try:
            ltv = await self._calculate_ltv(loan_id, session)
            if ltv is None:
                return
            
            # Get all positions
            result = await session.execute(
                select(CollateralPosition).where(CollateralPosition.loan_id == loan_id)
            )
            positions = result.scalars().all()
            
            total_value = sum(float(pos.value_usd) for pos in positions)
            
            for pos in positions:
                pos.ltv_ratio = ltv
                # Health ratio: 1 - (LTV / max_LTV), assuming max LTV of 0.8
                max_ltv = 0.8
                pos.health_ratio = max(0, min(1, 1 - (ltv / max_ltv)))
            
            await session.commit()
        except Exception as e:
            logger.error(f"Error updating position metrics: {e}", exc_info=True)
            await session.rollback()


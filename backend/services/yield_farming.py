"""
Yield farming service for yield farming protocol integration
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from config.network import get_network_config

logger = get_logger(__name__)


class YieldFarmingService:
    """Service for yield farming protocol integration"""
    
    def __init__(self):
        """Initialize with network-aware chain ID"""
        self.network_config = get_network_config()
    
    def get_supported_protocols(self) -> List[Dict[str, Any]]:
        """Get supported protocols with network-aware chain ID"""
        # Supported protocols (placeholder data) - uses active network chain ID
        chain_id = self.network_config.chain_id
        return [
            {
                "id": "qie_yield",
                "name": "QIE Yield Protocol",
                "chain_id": chain_id,
                "pools": [
                    {
                        "id": "qie_usdt",
                        "name": "QIE/USDT Pool",
                        "token0": "QIE",
                        "token1": "USDT",
                        "apy": 15.0,
                        "min_deposit": 100,
                    },
                    {
                        "id": "qie_usdc",
                        "name": "QIE/USDC Pool",
                        "token0": "QIE",
                        "token1": "USDC",
                        "apy": 14.5,
                        "min_deposit": 100,
                    },
                ],
            },
            {
                "id": "liquidity_pools",
                "name": "Liquidity Pools",
                "chain_id": chain_id,
                "pools": [
                    {
                        "id": "lp_qie_eth",
                        "name": "QIE/ETH LP",
                        "token0": "QIE",
                        "token1": "ETH",
                        "apy": 20.0,
                        "min_deposit": 500,
                    },
                ],
            },
        ]
    
    async def get_protocols(self) -> List[Dict[str, Any]]:
        """
        Get available yield farming protocols
        
        Returns:
            List of protocol dicts
        """
        try:
            return [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "chain_id": p["chain_id"],
                    "pool_count": len(p.get("pools", [])),
                }
                for p in self.get_supported_protocols()
            ]
        except Exception as e:
            logger.error(f"Error getting protocols: {e}", exc_info=True)
            return []
    
    async def get_pools(
        self,
        protocol: str
    ) -> List[Dict[str, Any]]:
        """
        Get available pools for a protocol
        
        Args:
            protocol: Protocol ID
            
        Returns:
            List of pool dicts
        """
        try:
            protocol_info = next(
                (p for p in self.get_supported_protocols() if p["id"] == protocol),
                None
            )
            
            if not protocol_info:
                return []
            
            return protocol_info.get("pools", [])
        except Exception as e:
            logger.error(f"Error getting pools: {e}", exc_info=True)
            return []
    
    async def calculate_apy(
        self,
        pool_id: str
    ) -> Optional[float]:
        """
        Calculate current APY for a pool
        
        Args:
            pool_id: Pool ID
            
        Returns:
            Current APY percentage
        """
        try:
            # Find pool
            for protocol in self.get_supported_protocols():
                pool = next(
                    (p for p in protocol.get("pools", []) if p["id"] == pool_id),
                    None
                )
                if pool:
                    return pool.get("apy", 0.0)
            
            return None
        except Exception as e:
            logger.error(f"Error calculating APY: {e}", exc_info=True)
            return None
    
    async def deposit_to_pool(
        self,
        pool_id: str,
        amount: Decimal,
        address: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Deposit to a yield pool
        
        Args:
            pool_id: Pool ID
            amount: Deposit amount
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Deposit transaction dict
        """
        try:
            # Find pool
            pool_info = None
            for protocol in self.get_supported_protocols():
                pool = next(
                    (p for p in protocol.get("pools", []) if p["id"] == pool_id),
                    None
                )
                if pool:
                    pool_info = pool
                    break
            
            if not pool_info:
                logger.warning(f"Pool not found: {pool_id}")
                return None
            
            # Check minimum deposit
            min_deposit = Decimal(str(pool_info.get("min_deposit", 0)))
            if amount < min_deposit:
                logger.warning(f"Amount below minimum deposit: {amount} < {min_deposit}")
                return None
            
            # In production, would interact with smart contract
            # For now, create a yield strategy record
            from database.connection import get_session
            from database.models import YieldStrategy
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_yield_strategy(
                        address, pool_id, amount, pool_info, db_session
                    )
            else:
                return await self._create_yield_strategy(
                    address, pool_id, amount, pool_info, session
                )
        except Exception as e:
            logger.error(f"Error depositing to pool: {e}", exc_info=True)
            return None
    
    async def _create_yield_strategy(
        self,
        address: str,
        pool_id: str,
        amount: Decimal,
        pool_info: Dict[str, Any],
        session
    ) -> Optional[Dict[str, Any]]:
        """Create yield strategy record"""
        from database.models import YieldStrategy
        from datetime import datetime
        
        try:
            strategy = YieldStrategy(
                wallet_address=address,
                strategy_type="yield_farming",
                protocol=pool_info.get("name", "Unknown"),
                token_address=pool_id,  # Use pool_id as token identifier
                amount=amount,
                apy=Decimal(str(pool_info.get("apy", 0))),
                auto_compound_enabled=False,
                total_rewards=Decimal('0'),
            )
            session.add(strategy)
            await session.commit()
            
            logger.info(f"Created yield strategy for pool {pool_id}, amount {amount}")
            
            return {
                "strategy_id": strategy.id,
                "pool_id": pool_id,
                "amount": float(amount),
                "apy": float(strategy.apy) if strategy.apy else None,
                "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _create_yield_strategy: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def withdraw_from_pool(
        self,
        pool_id: str,
        amount: Decimal,
        address: str,
        session=None
    ) -> bool:
        """
        Withdraw from a yield pool
        
        Args:
            pool_id: Pool ID
            amount: Withdraw amount
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            True if withdrawn successfully
        """
        try:
            from database.connection import get_session
            from database.models import YieldStrategy
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._withdraw_from_pool(pool_id, amount, address, db_session)
            else:
                return await self._withdraw_from_pool(pool_id, amount, address, session)
        except Exception as e:
            logger.error(f"Error withdrawing from pool: {e}", exc_info=True)
            return False
    
    async def _withdraw_from_pool(
        self,
        pool_id: str,
        amount: Decimal,
        address: str,
        session
    ) -> bool:
        """Withdraw from pool in database"""
        from database.models import YieldStrategy
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(YieldStrategy).where(
                    YieldStrategy.wallet_address == address,
                    YieldStrategy.token_address == pool_id,
                    YieldStrategy.strategy_type == "yield_farming"
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                logger.warning(f"Strategy not found for pool {pool_id}")
                return False
            
            if Decimal(str(strategy.amount)) < amount:
                logger.warning(f"Insufficient balance: {strategy.amount} < {amount}")
                return False
            
            # Update amount
            strategy.amount -= amount
            strategy.updated_at = datetime.utcnow()
            
            # Delete if zero
            if strategy.amount <= 0:
                await session.delete(strategy)
            
            await session.commit()
            
            logger.info(f"Withdrew {amount} from pool {pool_id}")
            return True
        except Exception as e:
            logger.error(f"Error in _withdraw_from_pool: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def harvest_rewards(
        self,
        pool_id: str,
        address: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Harvest rewards from a pool
        
        Args:
            pool_id: Pool ID
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Harvest transaction dict
        """
        try:
            from database.connection import get_session
            from database.models import YieldStrategy
            from sqlalchemy import select
            from datetime import datetime
            
            if session is None:
                async with get_session() as db_session:
                    return await self._harvest_rewards(pool_id, address, db_session)
            else:
                return await self._harvest_rewards(pool_id, address, session)
        except Exception as e:
            logger.error(f"Error harvesting rewards: {e}", exc_info=True)
            return None
    
    async def _harvest_rewards(
        self,
        pool_id: str,
        address: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Harvest rewards in database"""
        from database.models import YieldStrategy
        from sqlalchemy import select
        from datetime import datetime
        
        try:
            result = await session.execute(
                select(YieldStrategy).where(
                    YieldStrategy.wallet_address == address,
                    YieldStrategy.token_address == pool_id,
                    YieldStrategy.strategy_type == "yield_farming"
                )
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return None
            
            # Calculate rewards (simplified)
            if strategy.apy:
                # Calculate time since last update
                time_since = datetime.utcnow() - (strategy.updated_at or strategy.created_at)
                hours = time_since.total_seconds() / 3600
                
                apy_decimal = Decimal(str(strategy.apy))
                principal = Decimal(str(strategy.amount))
                rewards = principal * (apy_decimal / Decimal('100')) * (Decimal(str(hours)) / Decimal('8760'))
            else:
                rewards = Decimal('0')
            
            # Update total rewards
            strategy.total_rewards += rewards
            strategy.updated_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Harvested {rewards} rewards from pool {pool_id}")
            
            return {
                "pool_id": pool_id,
                "rewards": float(rewards),
                "total_rewards": float(strategy.total_rewards),
            }
        except Exception as e:
            logger.error(f"Error in _harvest_rewards: {e}", exc_info=True)
            await session.rollback()
            return None


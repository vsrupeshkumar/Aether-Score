"""
Oracle Price History Service

Tracks price history from QIE oracles for volatility calculations.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from web3 import Web3

from database.models import UserData
from database.connection import get_db_session
from services.oracle import QIEOracleService
from utils.logger import get_logger
from utils.cache import cache_get, cache_set
import json
import statistics

logger = get_logger(__name__)


class OraclePriceHistory:
    """Service for tracking and retrieving oracle price history"""
    
    def __init__(self):
        self.oracle_service = QIEOracleService()
        self.history_ttl = int(os.getenv("ORACLE_HISTORY_TTL", "86400"))  # 24 hours
        self.max_history_days = int(os.getenv("ORACLE_MAX_HISTORY_DAYS", "90"))
    
    async def record_price(self, asset: str, price: float, oracle_type: str = 'crypto') -> bool:
        """
        Record a price point in history
        
        Args:
            asset: Asset symbol
            price: Price value
            oracle_type: Type of oracle
            
        Returns:
            Success status
        """
        try:
            timestamp = datetime.now()
            price_key = f"oracle_price_{oracle_type}_{asset}"
            
            # Get existing history
            async with get_db_session() as session:
                from database.repositories import UserDataRepository
                
                # Store in a system record (using a special address)
                system_address = "0x0000000000000000000000000000000000000000"
                
                existing_data = await UserDataRepository.get_user_data(session, system_address)
                
                history = []
                if existing_data and existing_data.data_key == price_key:
                    history = json.loads(existing_data.data_value)
                
                # Add new price point
                history.append({
                    "timestamp": timestamp.isoformat(),
                    "price": price
                })
                
                # Keep only recent history
                cutoff_date = timestamp - timedelta(days=self.max_history_days)
                history = [
                    h for h in history
                    if datetime.fromisoformat(h["timestamp"]) > cutoff_date
                ]
                
                # Store updated history
                await UserDataRepository.upsert_user_data(
                    session,
                    system_address,
                    price_key,
                    json.dumps(history)
                )
                
                await session.commit()
            
            # Cache latest price
            cache_key = f"oracle_price_latest:{oracle_type}:{asset}"
            cache_set(cache_key, price, ttl=self.history_ttl)
            
            logger.debug(f"Recorded price for {asset}: {price}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording price: {e}", exc_info=True)
            return False
    
    async def get_price_history(
        self,
        asset: str,
        days: int = 30,
        oracle_type: str = 'crypto'
    ) -> List[Dict[str, Any]]:
        """
        Get price history for an asset
        
        Args:
            asset: Asset symbol
            days: Number of days of history
            oracle_type: Type of oracle
            
        Returns:
            List of price points
        """
        try:
            price_key = f"oracle_price_{oracle_type}_{asset}"
            system_address = "0x0000000000000000000000000000000000000000"
            
            async with get_db_session() as session:
                from database.repositories import UserDataRepository
                user_data = await UserDataRepository.get_user_data(session, system_address)
                
                if user_data and user_data.data_key == price_key:
                    history = json.loads(user_data.data_value)
                    
                    # Filter by days
                    cutoff_date = datetime.now() - timedelta(days=days)
                    filtered_history = [
                        h for h in history
                        if datetime.fromisoformat(h["timestamp"]) > cutoff_date
                    ]
                    
                    return filtered_history
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting price history: {e}", exc_info=True)
            return []
    
    async def calculate_volatility(
        self,
        asset: str,
        days: int = 30,
        oracle_type: str = 'crypto'
    ) -> Optional[float]:
        """
        Calculate volatility from price history
        
        Args:
            asset: Asset symbol
            days: Number of days for calculation
            oracle_type: Type of oracle
            
        Returns:
            Volatility as decimal (e.g., 0.25 for 25%)
        """
        try:
            history = await self.get_price_history(asset, days, oracle_type)
            
            if len(history) < 2:
                # Not enough data, fetch current price and estimate
                current_price = await self.oracle_service.get_price(asset, oracle_type)
                if current_price:
                    await self.record_price(asset, current_price, oracle_type)
                return 0.2  # Default volatility
            
            # Calculate returns
            prices = [h["price"] for h in history]
            returns = []
            
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(ret)
            
            if len(returns) < 2:
                return 0.2  # Default volatility
            
            # Calculate standard deviation of returns
            std_dev = statistics.stdev(returns)
            
            # Annualize (assuming daily returns)
            volatility = std_dev * (365 ** 0.5)
            
            logger.debug(f"Calculated volatility for {asset}: {volatility}")
            return volatility
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}", exc_info=True)
            return None
    
    async def update_price_history(self, assets: List[str], oracle_type: str = 'crypto') -> Dict[str, bool]:
        """
        Update price history for multiple assets
        
        Args:
            assets: List of asset symbols
            oracle_type: Type of oracle
            
        Returns:
            Dict mapping asset to success status
        """
        results = {}
        
        for asset in assets:
            try:
                price = await self.oracle_service.get_price(asset, oracle_type)
                if price:
                    success = await self.record_price(asset, price, oracle_type)
                    results[asset] = success
                else:
                    results[asset] = False
            except Exception as e:
                logger.warning(f"Error updating price for {asset}: {e}")
                results[asset] = False
        
        return results


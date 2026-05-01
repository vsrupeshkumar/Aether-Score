import os
from typing import Dict, Optional
from web3 import Web3
import requests
from dotenv import load_dotenv
from config.network import get_network_config, get_healthy_rpc_urls

load_dotenv()

class QIEOracleService:
    """Service for interacting with QIE Oracles"""
    
    def __init__(self):
        # Use centralized network configuration
        self.network_config = get_network_config()
        healthy_rpcs = get_healthy_rpc_urls(self.network_config)
        self.rpc_url = healthy_rpcs[0] if healthy_rpcs else self.network_config.get_primary_rpc()
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        # QIE has 7 oracles - these are example addresses (update with actual QIE oracle addresses)
        self.oracle_addresses = {
            'forex': os.getenv("QIE_FOREX_ORACLE", "0x0000000000000000000000000000000000000000"),
            'commodity': os.getenv("QIE_COMMODITY_ORACLE", "0x0000000000000000000000000000000000000000"),
            'crypto': os.getenv("QIE_CRYPTO_ORACLE", "0x0000000000000000000000000000000000000000"),
        }
    
    async def get_price(self, asset: str, oracle_type: str = 'crypto') -> Optional[float]:
        """
        Get price from QIE Oracle
        
        Args:
            asset: Asset symbol (e.g., 'ETH', 'BTC', 'USDT')
            oracle_type: Type of oracle ('forex', 'commodity', 'crypto')
        
        Returns:
            Price in USD or None if unavailable
        """
        try:
            # In production, this would call the actual QIE oracle contract
            # For now, we'll use a fallback to fetch from public APIs
            # This demonstrates the integration pattern
            
            # Try to get from QIE oracle contract first
            oracle_address = self.oracle_addresses.get(oracle_type)
            if oracle_address and oracle_address != "0x0000000000000000000000000000000000000000":
                try:
                    price = await self._call_oracle_contract(oracle_address)
                    if price:
                        return price
                except Exception as e:
                    from utils.logger import get_logger
                    logger = get_logger(__name__)
                    logger.warning(f"Oracle contract call failed: {e}, using fallback", extra={"error": str(e)})
            
            # Fallback to public API (for demo purposes)
            return await self._fetch_price_fallback(asset)
            
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error fetching price from oracle: {e}", exc_info=True)
            return None
    
    async def _call_oracle_contract(self, oracle_address: str) -> Optional[float]:
        """
        Call QIE oracle contract to get price
        
        Args:
            oracle_address: Address of the oracle contract
            
        Returns:
            Price in USD or None
        """
        try:
            # QIE Oracle ABI (simplified - update with actual ABI)
            oracle_abi = [
                {
                    "inputs": [],
                    "name": "latestAnswer",
                    "outputs": [{"internalType": "int256", "name": "", "type": "int256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            oracle_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(oracle_address),
                abi=oracle_abi
            )
            
            # Get latest answer
            raw_price = oracle_contract.functions.latestAnswer().call()
            decimals = oracle_contract.functions.decimals().call()
            
            # Convert to float
            price = float(raw_price) / (10 ** decimals)
            
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.debug(f"Fetched price from oracle contract: {price}")
            
            return price
            
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Error calling oracle contract: {e}")
            return None
    
    async def _fetch_price_fallback(self, asset: str) -> Optional[float]:
        """Fallback method to fetch prices from public APIs"""
        try:
            # Use CoinGecko or similar API as fallback
            asset_lower = asset.lower()
            
            # Map common assets
            asset_map = {
                'eth': 'ethereum',
                'btc': 'bitcoin',
                'usdt': 'tether',
                'usdc': 'usd-coin',
                'qie': 'qie',  # QIE token
            }
            
            coin_id = asset_map.get(asset_lower, asset_lower)
            
            # Try CoinGecko API
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if coin_id in data and 'usd' in data[coin_id]:
                    return float(data[coin_id]['usd'])
            
            return None
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Error in price fallback: {e}", extra={"error": str(e)})
            return None
    
    async def get_volatility(self, asset: str, days: int = 30) -> Optional[float]:
        """
        Calculate volatility from price history
        
        Args:
            asset: Asset symbol
            days: Number of days to calculate volatility
        
        Returns:
            Volatility as a decimal (e.g., 0.25 for 25%)
        """
        try:
            # Use price history service for real volatility calculation
            from services.oracle_price_history import OraclePriceHistory
            price_history = OraclePriceHistory()
            
            volatility = await price_history.calculate_volatility(asset, days, 'crypto')
            
            if volatility is not None:
                return volatility
            
            # Fallback to estimated volatility
            current_price = await self.get_price(asset)
            if not current_price:
                return 0.2  # Default volatility
            
            # Record current price for future calculations
            await price_history.record_price(asset, current_price, 'crypto')
            
            # Estimate volatility based on asset type
            volatility_map = {
                'usdt': 0.01,  # Stablecoins have low volatility
                'usdc': 0.01,
                'eth': 0.30,   # ETH has moderate volatility
                'btc': 0.35,   # BTC has higher volatility
            }
            
            asset_lower = asset.lower()
            return volatility_map.get(asset_lower, 0.25)  # Default 25%
            
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Error calculating volatility: {e}, using default", extra={"error": str(e)})
            return 0.2  # Default volatility
    
    async def get_forex_rate(self, pair: str) -> Optional[float]:
        """
        Get forex rate from QIE Forex Oracle
        
        Args:
            pair: Forex pair (e.g., 'USD/EUR', 'USD/GBP')
        
        Returns:
            Exchange rate or None
        """
        try:
            # In production, call QIE Forex Oracle contract
            # For demo, use fallback API
            if '/' in pair:
                base, quote = pair.split('/')
                # Use a forex API as fallback
                # This is just for demonstration
                return 1.0  # Placeholder
            return None
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error fetching forex rate: {e}", exc_info=True)
            return None
    
    async def get_commodity_price(self, commodity: str) -> Optional[float]:
        """
        Get commodity price from QIE Commodity Oracle
        
        Args:
            commodity: Commodity symbol (e.g., 'GOLD', 'OIL')
        
        Returns:
            Price in USD or None
        """
        try:
            # In production, call QIE Commodity Oracle contract
            # For demo, return placeholder
            return None
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error fetching commodity price: {e}", exc_info=True)
            return None


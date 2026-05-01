"""
Chain registry service for managing supported blockchain networks
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from utils.logger import get_logger
from config.network import get_network_config, QIE_TESTNET_CONFIG, QIE_MAINNET_CONFIG

logger = get_logger(__name__)


@dataclass
class ChainInfo:
    """Chain information"""
    chain_id: int
    name: str
    rpc_url: str
    explorer_url: Optional[str] = None
    native_currency: str = "ETH"
    enabled: bool = True


class ChainRegistry:
    """Registry for managing supported blockchain networks"""
    
    # QIE Testnet configuration (uses centralized network config)
    @staticmethod
    def _get_qie_testnet() -> ChainInfo:
        """Get QIE Testnet config from centralized network config"""
        config = QIE_TESTNET_CONFIG
        return ChainInfo(
            chain_id=config.chain_id,
            name=config.name,
            rpc_url=config.get_primary_rpc(),
            explorer_url=config.explorer_url,
            native_currency=config.native_currency,
            enabled=True
        )
    
    # QIE Mainnet configuration (uses centralized network config)
    @staticmethod
    def _get_qie_mainnet() -> ChainInfo:
        """Get QIE Mainnet config from centralized network config"""
        config = QIE_MAINNET_CONFIG
        return ChainInfo(
            chain_id=config.chain_id,
            name=config.name,
            rpc_url=config.get_primary_rpc(),
            explorer_url=config.explorer_url,
            native_currency=config.native_currency,
            enabled=True
        )
    
    # Lazy initialization to use network config
    @property
    def QIE_TESTNET(self) -> ChainInfo:
        """QIE Testnet configuration"""
        return self._get_qie_testnet()
    
    @property
    def QIE_MAINNET(self) -> ChainInfo:
        """QIE Mainnet configuration"""
        return self._get_qie_mainnet()
    
    # Common EVM chains (for future extensibility)
    ETHEREUM_MAINNET = ChainInfo(
        chain_id=1,
        name="Ethereum Mainnet",
        rpc_url="https://eth.llamarpc.com",
        explorer_url="https://etherscan.io",
        native_currency="ETH",
        enabled=False
    )
    
    POLYGON_MAINNET = ChainInfo(
        chain_id=137,
        name="Polygon",
        rpc_url="https://polygon.llamarpc.com",
        explorer_url="https://polygonscan.com",
        native_currency="MATIC",
        enabled=False
    )
    
    BSC_MAINNET = ChainInfo(
        chain_id=56,
        name="BNB Smart Chain",
        rpc_url="https://bsc-dataseed.binance.org",
        explorer_url="https://bscscan.com",
        native_currency="BNB",
        enabled=False
    )
    
    ARBITRUM_ONE = ChainInfo(
        chain_id=42161,
        name="Arbitrum One",
        rpc_url="https://arb1.arbitrum.io/rpc",
        explorer_url="https://arbiscan.io",
        native_currency="ETH",
        enabled=False
    )
    
    OPTIMISM_MAINNET = ChainInfo(
        chain_id=10,
        name="Optimism",
        rpc_url="https://mainnet.optimism.io",
        explorer_url="https://optimistic.etherscan.io",
        native_currency="ETH",
        enabled=False
    )
    
    def __init__(self):
        """Initialize chain registry"""
        # Initialize QIE chains from network config
        qie_testnet = self._get_qie_testnet()
        qie_mainnet = self._get_qie_mainnet()
        
        self._chains: Dict[int, ChainInfo] = {
            qie_testnet.chain_id: qie_testnet,
            qie_mainnet.chain_id: qie_mainnet,
            self.ETHEREUM_MAINNET.chain_id: self.ETHEREUM_MAINNET,
            self.POLYGON_MAINNET.chain_id: self.POLYGON_MAINNET,
            self.BSC_MAINNET.chain_id: self.BSC_MAINNET,
            self.ARBITRUM_ONE.chain_id: self.ARBITRUM_ONE,
            self.OPTIMISM_MAINNET.chain_id: self.OPTIMISM_MAINNET,
        }
    
    def get_chain_info(self, chain_id: int) -> Optional[ChainInfo]:
        """
        Get chain information by chain ID
        
        Args:
            chain_id: Chain identifier
            
        Returns:
            ChainInfo if found, None otherwise
        """
        return self._chains.get(chain_id)
    
    def get_supported_chains(self, enabled_only: bool = True) -> List[ChainInfo]:
        """
        Get list of supported chains
        
        Args:
            enabled_only: If True, only return enabled chains
            
        Returns:
            List of ChainInfo objects
        """
        chains = list(self._chains.values())
        if enabled_only:
            chains = [chain for chain in chains if chain.enabled]
        return chains
    
    def get_rpc_url(self, chain_id: int) -> Optional[str]:
        """
        Get RPC URL for a chain
        
        Args:
            chain_id: Chain identifier
            
        Returns:
            RPC URL if chain is supported, None otherwise
        """
        chain_info = self.get_chain_info(chain_id)
        return chain_info.rpc_url if chain_info else None
    
    def is_supported(self, chain_id: int) -> bool:
        """
        Check if chain is supported
        
        Args:
            chain_id: Chain identifier
            
        Returns:
            True if chain is supported and enabled
        """
        chain_info = self.get_chain_info(chain_id)
        return chain_info is not None and chain_info.enabled
    
    def register_chain(self, chain_info: ChainInfo) -> bool:
        """
        Register a new chain (for extensibility)
        
        Args:
            chain_info: Chain information
            
        Returns:
            True if registered successfully
        """
        try:
            self._chains[chain_info.chain_id] = chain_info
            logger.info(f"Registered chain: {chain_info.name} (ID: {chain_info.chain_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to register chain: {e}", exc_info=True)
            return False
    
    def get_default_chain(self) -> ChainInfo:
        """
        Get default chain (uses active network config)
        
        Returns:
            Default ChainInfo based on QIE_NETWORK env var
        """
        network_config = get_network_config()
        if network_config.is_mainnet:
            return self._get_qie_mainnet()
        else:
            return self._get_qie_testnet()


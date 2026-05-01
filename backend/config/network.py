"""
Centralized network configuration for QIE testnet and mainnet.

This module provides a single source of truth for network-specific settings,
allowing the application to switch between testnet and mainnet via environment variables.
"""
import os
from dataclasses import dataclass
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NetworkConfig:
    """Network configuration for QIE blockchain"""
    chain_id: int
    name: str
    rpc_urls: List[str]  # Multiple URLs for failover
    explorer_url: str
    native_currency: str
    symbol: str
    is_mainnet: bool = False
    
    def get_primary_rpc(self) -> str:
        """Get primary RPC URL"""
        return self.rpc_urls[0] if self.rpc_urls else ""
    
    def get_fallback_rpcs(self) -> List[str]:
        """Get fallback RPC URLs"""
        return self.rpc_urls[1:] if len(self.rpc_urls) > 1 else []


# QIE Testnet Configuration
QIE_TESTNET_CONFIG = NetworkConfig(
    chain_id=1983,
    name="QIE Testnet",
    rpc_urls=[
        "https://rpc1testnet.qie.digital/",
    ],
    explorer_url="https://testnet.qie.digital",
    native_currency="QIE",
    symbol="QIE",
    is_mainnet=False
)

# QIE Mainnet Configuration (Confirmed values)
QIE_MAINNET_CONFIG = NetworkConfig(
    chain_id=1990,
    name="QIEMainnet",
    rpc_urls=[
        "https://rpc1mainnet.qie.digital/",
        "https://rpc2mainnet.qie.digital/",
        "https://rpc5mainnet.qie.digital/",
    ],
    explorer_url="https://mainnet.qie.digital/",
    native_currency="QIEV3",
    symbol="QIEV3",
    is_mainnet=True
)


def get_network_config() -> NetworkConfig:
    """
    Get network configuration based on environment variable.
    
    Reads QIE_NETWORK environment variable:
    - "mainnet" -> Returns QIE_MAINNET_CONFIG
    - "testnet" or not set -> Returns QIE_TESTNET_CONFIG (default)
    
    Returns:
        NetworkConfig for the active network
    """
    network = os.getenv("QIE_NETWORK", "testnet").lower().strip()
    
    if network == "mainnet":
        config = QIE_MAINNET_CONFIG
        logger.info(
            "Using QIE Mainnet configuration",
            extra={
                "chain_id": config.chain_id,
                "network_name": config.name,  # Renamed from 'name' - reserved in LogRecord
                "rpc_urls": config.rpc_urls,
                "explorer_url": config.explorer_url,
            }
        )
        return config
    else:
        config = QIE_TESTNET_CONFIG
        logger.info(
            "Using QIE Testnet configuration",
            extra={
                "chain_id": config.chain_id,
                "network_name": config.name,  # Renamed from 'name' - reserved in LogRecord
                "rpc_urls": config.rpc_urls,
                "explorer_url": config.explorer_url,
            }
        )
        return config


def validate_rpc_health(rpc_url: str, timeout: int = 5) -> bool:
    """
    Validate RPC endpoint health by making a simple call.
    
    Args:
        rpc_url: RPC endpoint URL to check
        timeout: Request timeout in seconds
        
    Returns:
        True if RPC is healthy, False otherwise
    """
    try:
        from web3 import Web3
        
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": timeout}))
        # Try to get latest block number
        block_number = w3.eth.block_number
        return block_number is not None
    except Exception as e:
        logger.warning(f"RPC health check failed for {rpc_url}: {e}")
        return False


def get_healthy_rpc_urls(config: Optional[NetworkConfig] = None) -> List[str]:
    """
    Get list of healthy RPC URLs from network config.
    
    Args:
        config: NetworkConfig to use (defaults to get_network_config())
        
    Returns:
        List of healthy RPC URLs, falling back to all URLs if health check fails
    """
    if config is None:
        config = get_network_config()
    
    healthy_urls = []
    for rpc_url in config.rpc_urls:
        if validate_rpc_health(rpc_url):
            healthy_urls.append(rpc_url)
        else:
            logger.warning(f"RPC {rpc_url} failed health check, skipping")
    
    # If no healthy URLs found, return all URLs as fallback
    if not healthy_urls:
        logger.warning(
            "No healthy RPCs found, using all URLs as fallback",
            extra={"rpc_urls": config.rpc_urls}
        )
        return config.rpc_urls
    
    return healthy_urls


# Export for easy access
__all__ = [
    "NetworkConfig",
    "QIE_TESTNET_CONFIG",
    "QIE_MAINNET_CONFIG",
    "get_network_config",
    "validate_rpc_health",
    "get_healthy_rpc_urls",
]


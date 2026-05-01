"""
Bridge detection service for detecting cross-chain bridge transactions
"""
from typing import Dict, Optional, List, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


class BridgeDetector:
    """Service for detecting bridge transactions and linking addresses across chains"""
    
    # Known bridge contract addresses (can be extended)
    BRIDGE_CONTRACTS: Dict[str, Dict[str, str]] = {
        # Format: {chain_id: {contract_address: bridge_name}}
        "1983": {  # QIE Testnet
            # Add QIE bridge contracts when available
        },
        "1": {  # Ethereum Mainnet
            "0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f": "Hop Protocol",
            "0x3d4Cc8A61c7528Fd86C55cfe061a78DeCBAE7DAF": "Across Protocol",
            "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1": "Optimism Bridge",
        },
        "137": {  # Polygon
            "0x401F6c983ea34274ec46f84D70b31C151321188b": "Polygon Bridge",
        },
        "42161": {  # Arbitrum
            "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a": "Arbitrum Bridge",
        },
        "10": {  # Optimism
            "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1": "Optimism Bridge",
        },
    }
    
    # Bridge method signatures (first 4 bytes)
    BRIDGE_METHOD_SIGNATURES = {
        "0x9d1b464e",  # sendMessage (common bridge pattern)
        "0x38e52e78",  # deposit (common bridge pattern)
        "0x44cee73c",  # bridge (common bridge pattern)
        "0x7b3c71d3",  # sendToL2 (Optimism)
        "0x4e4d9fea",  # depositETH (Arbitrum)
    }
    
    def detect_bridge_transaction(
        self,
        tx_hash: str,
        contract_address: Optional[str],
        method_id: Optional[str],
        chain_id: int
    ) -> Optional[Dict[str, any]]:
        """
        Detect if a transaction is a bridge transaction
        
        Args:
            tx_hash: Transaction hash
            contract_address: Contract address interacted with
            method_id: Method signature (first 4 bytes)
            chain_id: Chain ID
            
        Returns:
            Bridge info dict if detected, None otherwise
        """
        if not contract_address or not method_id:
            return None
        
        # Check if contract is a known bridge
        chain_bridges = self.BRIDGE_CONTRACTS.get(str(chain_id), {})
        bridge_name = chain_bridges.get(contract_address.lower())
        
        if bridge_name:
            return {
                "is_bridge": True,
                "bridge_name": bridge_name,
                "contract_address": contract_address,
                "chain_id": chain_id,
                "tx_hash": tx_hash,
            }
        
        # Check method signature
        if method_id.lower() in self.BRIDGE_METHOD_SIGNATURES:
            return {
                "is_bridge": True,
                "bridge_name": "Unknown Bridge",
                "contract_address": contract_address,
                "chain_id": chain_id,
                "tx_hash": tx_hash,
                "detected_by": "method_signature",
            }
        
        return None
    
    def get_bridge_info(self, contract_address: str, chain_id: int) -> Optional[Dict[str, str]]:
        """
        Get bridge protocol information
        
        Args:
            contract_address: Bridge contract address
            chain_id: Chain ID
            
        Returns:
            Bridge info dict if found
        """
        chain_bridges = self.BRIDGE_CONTRACTS.get(str(chain_id), {})
        bridge_name = chain_bridges.get(contract_address.lower())
        
        if bridge_name:
            return {
                "name": bridge_name,
                "contract_address": contract_address,
                "chain_id": chain_id,
            }
        
        return None
    
    async def link_addresses_via_bridge(
        self,
        tx_hash: str,
        from_address: str,
        to_address: Optional[str],
        from_chain_id: int,
        to_chain_id: Optional[int],
        bridge_info: Dict[str, any]
    ) -> Optional[Tuple[str, str]]:
        """
        Link addresses across chains via bridge transaction
        
        Args:
            tx_hash: Bridge transaction hash
            from_address: Address on source chain
            to_address: Address on destination chain (if known)
            from_chain_id: Source chain ID
            to_chain_id: Destination chain ID (if known)
            bridge_info: Bridge detection info
            
        Returns:
            Tuple of (from_address, to_address) if linked, None otherwise
        """
        try:
            # For now, assume same address across EVM chains
            # In production, would parse bridge transaction logs to get destination address
            if to_address:
                return (from_address, to_address)
            
            # If same address (EVM chains), link them
            # This is a simplified approach - real implementation would parse bridge events
            if to_chain_id:
                return (from_address, from_address)  # Same address on different chain
            
            logger.warning(f"Bridge transaction detected but destination address unknown: {tx_hash}")
            return None
        except Exception as e:
            logger.error(f"Error linking addresses via bridge: {e}", exc_info=True)
            return None
    
    def is_bridge_contract(self, contract_address: str, chain_id: int) -> bool:
        """
        Check if an address is a known bridge contract
        
        Args:
            contract_address: Contract address to check
            chain_id: Chain ID
            
        Returns:
            True if known bridge contract
        """
        chain_bridges = self.BRIDGE_CONTRACTS.get(str(chain_id), {})
        return contract_address.lower() in chain_bridges


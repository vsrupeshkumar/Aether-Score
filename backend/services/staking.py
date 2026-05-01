import os
from web3 import Web3
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class StakingService:
    """Service for interacting with AETHER-SCOREStaking contract"""
    
    def __init__(self):
        self.rpc_url = os.getenv("QIE_RPC_URL") or os.getenv("QIE_TESTNET_RPC_URL", "https://rpc1testnet.qie.digital/")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.staking_address = os.getenv("STAKING_ADDRESS", "").strip()
        
        # Check if address is set and not a placeholder
        if (not self.staking_address or 
            self.staking_address.startswith("0xYour") or 
            self.staking_address == "0x0000000000000000000000000000000000000000" or
            "Your" in self.staking_address or
            "YOUR" in self.staking_address):
            # Staking is optional - service will return defaults if not configured
            self.staking_abi = self._get_staking_abi()
            self.staking_contract = None
            self.staking_address = None
        else:
            try:
                self.staking_abi = self._get_staking_abi()
                self.staking_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.staking_address),
                    abi=self.staking_abi
                )
            except Exception as e:
                from utils.logger import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Invalid staking address '{self.staking_address}': {e}. Staking disabled.", extra={"error": str(e)})
                self.staking_contract = None
                self.staking_address = None
    
    def _get_staking_abi(self) -> list:
        """Get AETHER-SCOREStaking contract ABI"""
        return [
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "integrationTier",
                "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "stakedAmount",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def get_staked_amount(self, address: str) -> int:
        """Get staked NCRD amount for an address"""
        if not self.staking_contract:
            return 0
        
        try:
            checksum_address = Web3.to_checksum_address(address)
            amount = self.staking_contract.functions.stakedAmount(checksum_address).call()
            return amount
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error getting staked amount: {e}", exc_info=True)
            return 0
    
    def get_integration_tier(self, address: str) -> int:
        """Get integration tier for an address (0-3)"""
        if not self.staking_contract:
            return 0
        
        try:
            checksum_address = Web3.to_checksum_address(address)
            tier = self.staking_contract.functions.integrationTier(checksum_address).call()
            return tier
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error getting integration tier: {e}", exc_info=True)
            return 0
    
    def calculate_staking_boost(self, tier: int) -> int:
        """
        Calculate score boost based on staking tier
        
        Tier mapping:
        - 0 (none): 0 points
        - 1 (Bronze): +50 points
        - 2 (Silver): +150 points
        - 3 (Gold): +300 points
        """
        boost_map = {
            0: 0,
            1: 50,
            2: 150,
            3: 300
        }
        return boost_map.get(tier, 0)



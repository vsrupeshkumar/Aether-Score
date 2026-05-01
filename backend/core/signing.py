"""
EIP-712 signature generation and verification for loan offers
Handles graceful degradation when private key is invalid or missing
"""
import os
from typing import Dict
from eth_account import Account
from eth_account.messages import encode_defunct, _hash_eip191_message
from eth_utils import keccak, to_checksum_address
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class LoanOfferSigner:
    """Handles EIP-712 signing of loan offers"""
    
    def __init__(self):
        # Use secrets manager for private key
        from utils.secrets_manager import get_secrets_manager
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        secrets_manager = get_secrets_manager()
        
        # Try to get encrypted private key, fallback to plaintext
        self.private_key = secrets_manager.get_secret("AI_SIGNER_PRIVATE_KEY_ENCRYPTED", encrypted=True)
        if not self.private_key:
            self.private_key = secrets_manager.get_secret("BACKEND_PRIVATE_KEY_ENCRYPTED", encrypted=True)
        if not self.private_key:
            self.private_key = os.getenv("AI_SIGNER_PRIVATE_KEY") or os.getenv("BACKEND_PK") or os.getenv("BACKEND_PRIVATE_KEY")
        
        # Initialize account and signing capability
        self.account = None
        self.can_sign = False
        
        if not self.private_key:
            logger.warning("No private key found. Loan offers will use placeholder signatures (demo mode).")
            self.can_sign = False
        else:
            # Sanitize private key: strip whitespace and ensure proper format
            private_key_clean = self.private_key.strip()
            # Remove any newlines or extra spaces
            private_key_clean = "".join(private_key_clean.split())
            
            # Validate format
            if not private_key_clean.startswith("0x"):
                # If missing 0x prefix, add it
                if len(private_key_clean) == 64:
                    private_key_clean = "0x" + private_key_clean
                else:
                    logger.warning(f"Invalid private key format: got length {len(private_key_clean)}. Loan offers will use placeholder signatures (demo mode).")
                    self.can_sign = False
                    private_key_clean = None
            
            if private_key_clean and len(private_key_clean) != 66:
                logger.warning(f"Invalid private key length: expected 66 characters, got {len(private_key_clean)}. Loan offers will use placeholder signatures (demo mode).")
                self.can_sign = False
                private_key_clean = None
            
            # Validate hex characters and create account
            if private_key_clean:
                try:
                    int(private_key_clean[2:], 16)
                    self.account = Account.from_key(private_key_clean)
                    self.can_sign = True
                    logger.info("Private key validated successfully. Loan offers will be signed.")
                except (ValueError, Exception) as e:
                    logger.warning(f"Invalid private key: {str(e)}. Loan offers will use placeholder signatures (demo mode).")
                    self.can_sign = False
                    self.account = None
        
        # Use centralized network configuration
        from config.network import get_network_config, get_healthy_rpc_urls
        self.network_config = get_network_config()
        healthy_rpcs = get_healthy_rpc_urls(self.network_config)
        self.rpc_url = healthy_rpcs[0] if healthy_rpcs else self.network_config.get_primary_rpc()
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Get chain ID from network config (with fallback to RPC)
        try:
            self.chain_id = self.w3.eth.chain_id
            # Verify chain ID matches config
            if self.chain_id != self.network_config.chain_id:
                from utils.logger import get_logger
                logger = get_logger(__name__)
                logger.warning(
                    f"Chain ID mismatch: RPC returned {self.chain_id}, config expects {self.network_config.chain_id}"
                )
        except:
            # Fallback to config chain ID
            self.chain_id = self.network_config.chain_id
    
    def get_domain_separator(self, contract_address: str) -> Dict:
        """Get EIP-712 domain separator"""
        return {
            "name": "NeuroLend LendingVault",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": to_checksum_address(contract_address)
        }
    
    def sign_loan_offer(self, offer: Dict, contract_address: str) -> str:
        """
        Sign a loan offer using EIP-712
        
        Args:
            offer: Loan offer dict with keys:
                - borrower: address
                - amount: uint256
                - collateralAmount: uint256
                - interestRate: uint256 (basis points)
                - duration: uint256 (seconds)
                - nonce: uint256
                - expiry: uint256 (timestamp)
            contract_address: LendingVault contract address
            
        Returns:
            Hex-encoded signature (or placeholder if signing is not available)
        """
        # If we can't sign, return a placeholder signature
        if not self.can_sign or not self.account:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning("Cannot sign loan offer - using placeholder signature (demo mode)")
            # Return a placeholder signature (130 hex chars = 65 bytes)
            return "0x" + "0" * 130
        # Validate addresses
        borrower = offer.get('borrower', '')
        if not borrower or not isinstance(borrower, str):
            raise ValueError(f"Invalid borrower address: {borrower}")
        
        # Sanitize addresses: strip whitespace
        borrower = borrower.strip()
        contract_address = contract_address.strip() if contract_address else ''
        
        # Validate hex format
        for addr_name, addr_value in [('borrower', borrower), ('contract', contract_address)]:
            if not addr_value.startswith('0x'):
                raise ValueError(f"Invalid {addr_name} address format: must start with 0x")
            if len(addr_value) != 42:
                raise ValueError(f"Invalid {addr_name} address length: expected 42 characters, got {len(addr_value)}")
            try:
                int(addr_value[2:], 16)
            except ValueError as e:
                raise ValueError(f"Invalid {addr_name} address: contains non-hexadecimal characters. Error: {str(e)}")
        
        # Update offer with sanitized borrower address
        offer = offer.copy()
        offer['borrower'] = borrower
        
        domain = self.get_domain_separator(contract_address)
        
        # EIP-712 type hash
        LOAN_OFFER_TYPEHASH = keccak(
            b"LoanOffer(address borrower,uint256 amount,uint256 collateralAmount,uint256 interestRate,uint256 duration,uint256 nonce,uint256 expiry)"
        )
        
        # Encode struct
        struct_hash = keccak(
            Web3.solidity_keccak(
                ['bytes32', 'address', 'uint256', 'uint256', 'uint256', 'uint256', 'uint256', 'uint256'],
                [
                    LOAN_OFFER_TYPEHASH,
                    to_checksum_address(offer['borrower']),
                    offer['amount'],
                    offer['collateralAmount'],
                    offer['interestRate'],
                    offer['duration'],
                    offer['nonce'],
                    offer['expiry']
                ]
            )
        )
        
        # EIP-712 message
        message = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "LoanOffer": [
                    {"name": "borrower", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "collateralAmount", "type": "uint256"},
                    {"name": "interestRate", "type": "uint256"},
                    {"name": "duration", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "expiry", "type": "uint256"}
                ]
            },
            "primaryType": "LoanOffer",
            "domain": domain,
            "message": offer
        }
        
        # Sign
        signed_message = Account.sign_message(
            encode_defunct(primitive=Web3.to_bytes(hexstr=Web3.to_hex(struct_hash))),
            self.account.key
        )
        
        return signed_message.signature.hex()
    
    def verify_signature(self, offer: Dict, signature: str, contract_address: str, expected_signer: str) -> bool:
        """
        Verify an EIP-712 signature
        
        Args:
            offer: Loan offer dict
            signature: Hex-encoded signature
            contract_address: Contract address
            expected_signer: Expected signer address
            
        Returns:
            True if signature is valid
        """
        try:
            domain = self.get_domain_separator(contract_address)
            
            LOAN_OFFER_TYPEHASH = keccak(
                b"LoanOffer(address borrower,uint256 amount,uint256 collateralAmount,uint256 interestRate,uint256 duration,uint256 nonce,uint256 expiry)"
            )
            
            struct_hash = keccak(
                Web3.solidity_keccak(
                    ['bytes32', 'address', 'uint256', 'uint256', 'uint256', 'uint256', 'uint256', 'uint256'],
                    [
                        LOAN_OFFER_TYPEHASH,
                        to_checksum_address(offer['borrower']),
                        offer['amount'],
                        offer['collateralAmount'],
                        offer['interestRate'],
                        offer['duration'],
                        offer['nonce'],
                        offer['expiry']
                    ]
                )
            )
            
            message_hash = keccak(
                b'\x19\x01' +
                Web3.solidity_keccak(
                    ['string', 'string', 'uint256', 'address'],
                    [
                        domain['name'],
                        domain['version'],
                        domain['chainId'],
                        to_checksum_address(contract_address)
                    ]
                ) +
                struct_hash
            )
            
            signer = Account.recover_message(
                encode_defunct(primitive=Web3.to_bytes(hexstr=Web3.to_hex(message_hash))),
                signature=signature
            )
            
            return signer.lower() == expected_signer.lower()
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False


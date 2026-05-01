import os
import time
from web3 import Web3
from eth_account import Account
from typing import Dict, Optional
from dotenv import load_dotenv
from config.network import get_network_config, get_healthy_rpc_urls

load_dotenv()

class BlockchainService:
    """Service for interacting with QIE blockchain"""
    
    def __init__(self):
        # Use centralized network configuration
        self.network_config = get_network_config()
        # Get healthy RPC URLs with failover support
        healthy_rpcs = get_healthy_rpc_urls(self.network_config)
        self.rpc_url = healthy_rpcs[0] if healthy_rpcs else self.network_config.get_primary_rpc()
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        # Accept both CREDIT_PASSPORT_NFT_ADDRESS and CREDIT_PASSPORT_ADDRESS for backward compatibility
        self.contract_address = os.getenv("CREDIT_PASSPORT_NFT_ADDRESS") or os.getenv("CREDIT_PASSPORT_ADDRESS")
        
        # Use secrets manager for private key
        from utils.secrets_manager import get_secrets_manager
        secrets_manager = get_secrets_manager()
        
        # Try to get encrypted private key, fallback to plaintext
        private_key = secrets_manager.get_secret("BACKEND_PRIVATE_KEY_ENCRYPTED", encrypted=True)
        if not private_key:
            private_key = os.getenv("BACKEND_PRIVATE_KEY")
        
        if not self.contract_address:
            raise ValueError("CREDIT_PASSPORT_NFT_ADDRESS or CREDIT_PASSPORT_ADDRESS must be set in environment")
        if not private_key:
            raise ValueError("BACKEND_PRIVATE_KEY not set in environment")
        
        self.account = Account.from_key(private_key)
        self.contract_abi = self._get_contract_abi()
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=self.contract_abi
        )
    
    def _get_contract_abi(self) -> list:
        """Get contract ABI - try to load from file, fallback to hardcoded minimal ABI"""
        import json
        from pathlib import Path
        
        # Try to load from ABI files (V1 or V2)
        abi_paths = [
            Path(__file__).parent.parent / "abis" / "CreditPassportNFT.json",  # V1
            Path(__file__).parent.parent / "abis" / "CreditPassportNFTV2.json",  # V2
        ]
        
        for abi_path in abi_paths:
            if abi_path.exists():
                try:
                    with open(abi_path, 'r') as f:
                        abi_data = json.load(f)
                        # Handle both direct ABI arrays and artifact format
                        if isinstance(abi_data, list):
                            abi = abi_data
                        elif isinstance(abi_data, dict) and "abi" in abi_data:
                            abi = abi_data["abi"]
                        else:
                            continue
                        
                        # Verify required functions exist
                        function_names = [item.get("name") for item in abi if item.get("type") == "function"]
                        if "mintOrUpdate" in function_names and "getScore" in function_names:
                            from utils.logger import get_logger
                            logger = get_logger(__name__)
                            logger.info(f"Loaded contract ABI from {abi_path.name}")
                            return abi
                except Exception as e:
                    from utils.logger import get_logger
                    logger = get_logger(__name__)
                    logger.warning(f"Failed to load ABI from {abi_path}: {e}")
                    continue
        
        # Fallback to hardcoded minimal ABI (matches CreditPassportNFT V1)
        # This ABI matches the actual deployed contract interface
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Using hardcoded minimal ABI (fallback)")
        return [
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"},
                          {"internalType": "uint16", "name": "score", "type": "uint16"},
                          {"internalType": "uint8", "name": "riskBand", "type": "uint8"}],
                "name": "mintOrUpdate",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
                "name": "getScore",
                "outputs": [
                    {
                        "components": [
                            {"internalType": "uint16", "name": "score", "type": "uint16"},
                            {"internalType": "uint8", "name": "riskBand", "type": "uint8"},
                            {"internalType": "uint64", "name": "lastUpdated", "type": "uint64"}
                        ],
                        "internalType": "struct IAETHER-SCOREScore.ScoreView",
                        "name": "",
                        "type": "tuple"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    async def get_score(self, address: str) -> Optional[Dict]:
        """Get score from blockchain"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            result = self.contract.functions.getScore(checksum_address).call()
            
            # Handle both tuple and struct return types
            # getScore returns a struct (ScoreView), which web3.py returns as a tuple
            if isinstance(result, tuple) and len(result) >= 3:
                score = result[0]
                risk_band = result[1]
                last_updated = result[2]
            elif isinstance(result, dict):
                # If returned as dict (shouldn't happen with current setup, but handle it)
                score = result.get("score", 0)
                risk_band = result.get("riskBand", 0)
                last_updated = result.get("lastUpdated", 0)
            else:
                from utils.logger import get_logger
                logger = get_logger(__name__)
                logger.error(f"Unexpected result type from getScore: {type(result)}")
                return None
            
            if score == 0:  # score is 0, no passport exists
                return None
            
            return {
                "score": score,
                "riskBand": risk_band,
                "lastUpdated": last_updated
            }
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error getting score from blockchain: {e}", exc_info=True)
            return None
    
    def _verify_mainnet_safety(self) -> None:
        """Verify we're ready for mainnet transaction"""
        if not self.network_config.is_mainnet:
            return  # No checks needed for testnet
        
        from utils.logger import get_logger
        logger = get_logger(__name__)
        
        # Check if mainnet transactions are allowed
        allow_mainnet = os.getenv("ALLOW_MAINNET_TRANSACTIONS", "false").lower() == "true"
        if not allow_mainnet:
            error_msg = "Mainnet transactions are disabled. Set ALLOW_MAINNET_TRANSACTIONS=true to enable."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check balance
        balance = self.w3.eth.get_balance(self.account.address)
        min_balance_wei = self.w3.to_wei(0.1, 'ether')  # Minimum 0.1 QIEV3
        if balance < min_balance_wei:
            error_msg = f"Insufficient balance for mainnet transaction. Required: {self.w3.from_wei(min_balance_wei, 'ether')} QIEV3, Available: {self.w3.from_wei(balance, 'ether')} QIEV3"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Log mainnet transaction attempt
        logger.warning(
            "Mainnet transaction attempt",
            extra={
                "address": self.account.address,
                "balance": str(balance),
                "balance_qiev3": self.w3.from_wei(balance, 'ether')
            }
        )
    
    async def update_score(self, address: str, score: int, risk_band: int) -> str:
        """Update score on blockchain with mainnet safeguards"""
        start_time = time.time()
        try:
            # Verify mainnet safety before proceeding
            self._verify_mainnet_safety()
            
            checksum_address = Web3.to_checksum_address(address)
            
            # Mainnet-specific safeguards
            gas_limit = 200000
            max_gas_price_gwei = 100  # Maximum gas price in Gwei for mainnet
            
            # Get current gas price
            current_gas_price = self.w3.eth.gas_price
            
            if self.network_config.is_mainnet:
                gas_price_gwei = current_gas_price / 1e9
                
                if gas_price_gwei > max_gas_price_gwei:
                    from utils.logger import get_logger
                    logger = get_logger(__name__)
                    logger.warning(
                        f"Gas price too high for mainnet: {gas_price_gwei:.2f} Gwei (max: {max_gas_price_gwei} Gwei)",
                        extra={"gas_price_gwei": gas_price_gwei, "max_gas_price_gwei": max_gas_price_gwei}
                    )
                    # Use max gas price instead
                    current_gas_price = int(max_gas_price_gwei * 1e9)
                
                # Estimate gas before building transaction (for mainnet safety)
                try:
                    estimated_gas = self.contract.functions.mintOrUpdate(
                        checksum_address,
                        score,
                        risk_band
                    ).estimate_gas({
                        'from': self.account.address
                    })
                    # Use estimated gas with 20% buffer, but cap at reasonable limit
                    gas_limit = min(int(estimated_gas * 1.2), 300000)  # Cap at 300k
                    from utils.logger import get_logger
                    logger = get_logger(__name__)
                    logger.info(f"Gas estimated: {estimated_gas}, using: {gas_limit}")
                except Exception as e:
                    from utils.logger import get_logger
                    logger = get_logger(__name__)
                    logger.warning(f"Gas estimation failed: {e}, using default {gas_limit}")
            
            # Build transaction
            transaction = self.contract.functions.mintOrUpdate(
                checksum_address,
                score,
                risk_band
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': gas_limit,
                'gasPrice': current_gas_price,
            })
            
            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Send transaction (use raw_transaction for newer web3.py, fallback to rawTransaction for older)
            raw_tx = getattr(signed_txn, 'raw_transaction', None) or getattr(signed_txn, 'rawTransaction', None)
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            
            # Wait for receipt with timeout (5 minutes max, more blocks for mainnet)
            timeout = 300  # 5 minutes
            required_confirmations = 3 if self.network_config.is_mainnet else 1
            
            receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash, 
                timeout=timeout
            )
            
            # Enhanced logging for mainnet
            from utils.logger import get_logger
            logger = get_logger(__name__)
            if self.network_config.is_mainnet:
                logger.info(
                    "Mainnet transaction submitted",
                    extra={
                        "tx_hash": receipt.transactionHash.hex(),
                        "address": address,
                        "score": score,
                        "risk_band": risk_band,
                        "gas_limit": gas_limit,
                        "gas_price_gwei": (current_gas_price / 1e9),
                        "gas_used": receipt.gasUsed,
                    }
                )
                
                # Verify confirmations for mainnet
                if receipt.blockNumber:
                    current_block = self.w3.eth.block_number
                    confirmations = current_block - receipt.blockNumber
                    if confirmations < required_confirmations:
                        logger.warning(
                            f"Insufficient confirmations: {confirmations} < {required_confirmations}",
                            extra={"tx_hash": receipt.transactionHash.hex(), "confirmations": confirmations}
                        )
            
            tx_hash_hex = receipt.transactionHash.hex()
            
            # Log transaction details (logger already defined above)
            transaction_duration = time.time() - start_time
            
            logger.info(
                "Transaction successful",
                extra={
                    "address": address,
                    "tx_hash": tx_hash_hex,
                    "gas_used": receipt.gasUsed,
                    "score": score,
                    "risk_band": risk_band,
                }
            )
            
            # Record metrics (if available)
            try:
                from utils.metrics import record_blockchain_transaction
                record_blockchain_transaction(
                    status="success",
                    contract="CreditPassportNFT",
                    operation="mintOrUpdate",
                    duration=transaction_duration,
                    gas_used=receipt.gasUsed
                )
            except ImportError:
                # Metrics not available in test environment
                pass
            
            # Invalidate caches for this address
            from utils.cache import invalidate_score_cache, invalidate_pattern
            invalidate_score_cache(address)
            invalidate_pattern(f"rpc:getScore:*{address}*")
            
            return tx_hash_hex
        except ValueError as e:
            # Handle invalid address format
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Invalid address format: {e}", exc_info=True)
            
            # Record error metrics (if available)
            try:
                from utils.metrics import record_blockchain_transaction, record_blockchain_rpc_error
                duration = time.time() - start_time
                error_type = type(e).__name__
                record_blockchain_rpc_error(error_type)
                record_blockchain_transaction(
                    status="error",
                    contract="CreditPassportNFT",
                    operation="mintOrUpdate",
                    duration=duration
                )
            except ImportError:
                # Metrics not available in test environment
                pass
            
            raise ValueError(f"Invalid address format: {str(e)}")
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Error updating score on blockchain: {e}", exc_info=True)
            
            # Record error metrics (if available)
            try:
                from utils.metrics import record_blockchain_transaction, record_blockchain_rpc_error
                duration = time.time() - start_time
                error_type = type(e).__name__
                record_blockchain_rpc_error(error_type)
                record_blockchain_transaction(
                    status="error",
                    contract="CreditPassportNFT",
                    operation="mintOrUpdate",
                    duration=duration
                )
            except ImportError:
                # Metrics not available in test environment
                pass
            
            raise Exception(f"Error updating score on blockchain: {str(e)}")



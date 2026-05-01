"""
On-chain proof service for generating verifiable on-chain proof URLs
"""
from typing import Dict, Optional, Any
from utils.logger import get_logger
from services.blockchain import BlockchainService

logger = get_logger(__name__)


class OnChainProofService:
    """Service for generating on-chain verification proofs"""
    
    def __init__(self):
        self.blockchain_service = BlockchainService()
    
    async def generate_verification_url(
        self,
        address: str
    ) -> str:
        """
        Generate verification URL with on-chain proof
        
        Args:
            address: Wallet address
            
        Returns:
            Verification URL string
        """
        try:
            import os
            from urllib.parse import urlencode
            
            # Get proof data
            proof_data = await self.generate_proof_data(address)
            
            if not proof_data.get("verified"):
                return ""
            
            # Get base URL
            base_url = os.getenv("FRONTEND_URL", "https://neuro-cred-git-main-diveshk007s-projects.vercel.app")
            
            # Create verification URL
            params = {
                "address": address,
                "token_id": proof_data.get("token_id", ""),
                "tx_hash": proof_data.get("tx_hash", ""),
            }
            
            verification_url = f"{base_url}/verify?{urlencode(params)}"
            
            return verification_url
        except Exception as e:
            logger.error(f"Error generating verification URL: {e}", exc_info=True)
            return ""
    
    async def verify_score_onchain(
        self,
        address: str
    ) -> bool:
        """
        Verify score exists on-chain
        
        Args:
            address: Wallet address
            
        Returns:
            True if score exists on-chain
        """
        try:
            on_chain_score = await self.blockchain_service.get_score(address)
            return on_chain_score is not None and on_chain_score.get("score", 0) > 0
        except Exception as e:
            logger.error(f"Error verifying score on-chain: {e}", exc_info=True)
            return False
    
    async def generate_proof_data(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Generate proof data (tx hash, contract address, etc.)
        
        Args:
            address: Wallet address
            
        Returns:
            Proof data dict
        """
        try:
            # Get on-chain score
            on_chain_score = await self.blockchain_service.get_score(address)
            
            if not on_chain_score:
                return {
                    "verified": False,
                    "address": address,
                    "message": "No on-chain score found",
                }
            
            # Get contract address
            contract_address = self.blockchain_service.contract_address
            
            # Get explorer URL
            explorer_url = self.blockchain_service.explorer_url
            
            # Get passport token ID
            token_id = None
            try:
                # Call passportIdOf function on contract
                token_id = await self.blockchain_service.contract.functions.passportIdOf(
                    address
                ).call()
                if token_id == 0:
                    token_id = None
            except Exception as e:
                logger.warning(f"Could not get passport ID: {e}")
                token_id = None
            
            # Get transaction hash (from last update)
            # In production, would query transaction history
            tx_hash = None
            
            # Build explorer link
            explorer_link = None
            if explorer_url and contract_address:
                explorer_link = f"{explorer_url}/address/{contract_address}"
            
            # Build token link
            token_link = None
            if explorer_url and token_id:
                # Link to NFT token page if explorer supports it
                token_link = f"{explorer_url}/token/{contract_address}/{token_id}"
            
            return {
                "verified": True,
                "address": address,
                "score": on_chain_score.get("score", 0),
                "risk_band": on_chain_score.get("riskBand", 0),
                "token_id": token_id,
                "contract_address": contract_address,
                "tx_hash": tx_hash,
                "explorer_link": explorer_link,
                "token_link": token_link,
                "verification_url": await self.generate_verification_url(address),
            }
        except Exception as e:
            logger.error(f"Error generating proof data: {e}", exc_info=True)
            return {
                "verified": False,
                "address": address,
                "error": str(e),
            }


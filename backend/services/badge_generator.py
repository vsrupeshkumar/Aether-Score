"""
Badge generator service for creating shareable credit score badges
"""
from typing import Dict, Optional, Any
from utils.logger import get_logger
from services.scoring import ScoringService
from services.blockchain import BlockchainService

logger = get_logger(__name__)


class BadgeGenerator:
    """Service for generating shareable credit score badges"""
    
    # Badge style configurations
    BADGE_STYLES = {
        "minimal": {
            "show_score": True,
            "show_risk_band": True,
            "show_explanation": False,
            "show_proof": False,
        },
        "detailed": {
            "show_score": True,
            "show_risk_band": True,
            "show_explanation": True,
            "show_proof": False,
        },
        "verified": {
            "show_score": True,
            "show_risk_band": True,
            "show_explanation": True,
            "show_proof": True,
        },
    }
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.blockchain_service = BlockchainService()
    
    async def generate_score_badge(
        self,
        address: str,
        style: str = "minimal"
    ) -> Dict[str, Any]:
        """
        Generate shareable badge image/data
        
        Args:
            address: Wallet address
            style: Badge style ('minimal', 'detailed', 'verified')
            
        Returns:
            Badge dict with image data and metadata
        """
        try:
            # Validate style
            if style not in self.BADGE_STYLES:
                style = "minimal"
            
            # Get score data
            badge_data = await self.generate_badge_data(address)
            
            # Generate badge based on style
            badge_config = self.BADGE_STYLES[style]
            
            # For now, return structured data that can be used to generate image
            # In production, would use PIL/Pillow or similar to generate actual image
            badge = {
                "address": address,
                "style": style,
                "score": badge_data.get("score", 0),
                "risk_band": badge_data.get("risk_band", 0),
                "risk_description": badge_data.get("risk_description", "Unknown"),
                "explanation": badge_data.get("explanation", "") if badge_config["show_explanation"] else None,
                "on_chain_proof": badge_data.get("on_chain_proof") if badge_config["show_proof"] else None,
                "badge_url": await self.create_shareable_url(address, badge_data),
                "metadata": {
                    "generated_at": badge_data.get("generated_at"),
                    "token_id": badge_data.get("token_id"),
                },
            }
            
            return badge
        except Exception as e:
            logger.error(f"Error generating score badge: {e}", exc_info=True)
            return {
                "address": address,
                "style": style,
                "error": "Failed to generate badge",
            }
    
    async def generate_badge_data(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Generate badge metadata (score, risk band, etc.)
        
        Args:
            address: Wallet address
            
        Returns:
            Badge data dict
        """
        try:
            # Get score
            score_result = await self.scoring_service.compute_score(address)
            score = score_result.get('score', 0)
            risk_band = score_result.get('riskBand', 0)
            
            # Get on-chain data
            on_chain_score = await self.blockchain_service.get_score(address)
            token_id = None
            tx_hash = None
            
            if on_chain_score:
                # Get token ID from blockchain
                try:
                    passport_id = await self.blockchain_service.get_passport_id(address)
                    token_id = passport_id
                except Exception as e:
                    logger.warning(f"Could not get passport ID: {e}")
            
            # Risk band descriptions
            risk_descriptions = {
                1: "Low Risk",
                2: "Medium Risk",
                3: "High Risk",
                0: "Unknown",
            }
            
            # Generate explanation
            explanation = score_result.get('explanation', '')
            
            # Get explorer URL
            explorer_url = self.blockchain_service.explorer_url
            verification_url = f"{explorer_url}/address/{address}" if explorer_url else None
            
            return {
                "address": address,
                "score": score,
                "risk_band": risk_band,
                "risk_description": risk_descriptions.get(risk_band, "Unknown"),
                "explanation": explanation,
                "on_chain_proof": {
                    "verified": on_chain_score is not None,
                    "token_id": token_id,
                    "tx_hash": tx_hash,
                    "verification_url": verification_url,
                } if on_chain_score else None,
                "generated_at": None,  # Will be set by caller
                "token_id": token_id,
            }
        except Exception as e:
            logger.error(f"Error generating badge data: {e}", exc_info=True)
            return {
                "address": address,
                "score": 0,
                "risk_band": 0,
                "risk_description": "Unknown",
                "explanation": "",
            }
    
    async def create_shareable_url(
        self,
        address: str,
        badge_data: Dict[str, Any]
    ) -> str:
        """
        Create shareable badge URL
        
        Args:
            address: Wallet address
            badge_data: Badge data dict
            
        Returns:
            Shareable URL string
        """
        try:
            import os
            from urllib.parse import urlencode
            
            # Get base URL from environment or use default
            base_url = os.getenv("FRONTEND_URL", "https://neuro-cred-git-main-diveshk007s-projects.vercel.app")
            
            # Create shareable URL with badge data
            params = {
                "address": address,
                "score": badge_data.get("score", 0),
                "risk_band": badge_data.get("risk_band", 0),
            }
            
            shareable_url = f"{base_url}/badge?{urlencode(params)}"
            
            return shareable_url
        except Exception as e:
            logger.error(f"Error creating shareable URL: {e}", exc_info=True)
            return ""


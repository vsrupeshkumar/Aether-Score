"""
Social media share service for generating platform-specific share content
"""
from typing import Dict, Optional, Any
from urllib.parse import quote, urlencode
from utils.logger import get_logger
from services.badge_generator import BadgeGenerator

logger = get_logger(__name__)


class SocialShareService:
    """Service for generating social media share content"""
    
    def __init__(self):
        self.badge_generator = BadgeGenerator()
    
    async def generate_twitter_share(
        self,
        address: str,
        badge_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate Twitter/X share text + image
        
        Args:
            address: Wallet address
            badge_data: Optional badge data (will fetch if not provided)
            
        Returns:
            Twitter share dict with text, image URL, and share URL
        """
        try:
            if not badge_data:
                badge_data = await self.badge_generator.generate_badge_data(address)
            
            score = badge_data.get("score", 0)
            risk_description = badge_data.get("risk_description", "Unknown")
            
            # Generate share text
            share_text = f"ðŸŽ¯ My AETHER-SCORE Credit Score: {score}/1000 ({risk_description})\n\n"
            share_text += f"Verified on-chain credit passport on QIE Network\n\n"
            share_text += f"#AETHER-SCORE #DeFi #QIE #CreditScore"
            
            # Get badge URL
            badge_url = await self.badge_generator.create_shareable_url(address, badge_data)
            
            # Generate Twitter share URL
            twitter_share_url = f"https://twitter.com/intent/tweet?{urlencode({'text': share_text, 'url': badge_url})}"
            
            return {
                "platform": "twitter",
                "share_text": share_text,
                "badge_url": badge_url,
                "share_url": twitter_share_url,
                "image_url": badge_url,  # Badge URL can be used as image
            }
        except Exception as e:
            logger.error(f"Error generating Twitter share: {e}", exc_info=True)
            return {
                "platform": "twitter",
                "error": "Failed to generate share",
            }
    
    async def generate_linkedin_share(
        self,
        address: str,
        badge_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate LinkedIn share
        
        Args:
            address: Wallet address
            badge_data: Optional badge data (will fetch if not provided)
            
        Returns:
            LinkedIn share dict with text, image URL, and share URL
        """
        try:
            if not badge_data:
                badge_data = await self.badge_generator.generate_badge_data(address)
            
            score = badge_data.get("score", 0)
            risk_description = badge_data.get("risk_description", "Unknown")
            explanation = badge_data.get("explanation", "")
            
            # Generate share text (LinkedIn allows longer text)
            share_text = f"My AETHER-SCORE Credit Score: {score}/1000 ({risk_description})\n\n"
            if explanation:
                share_text += f"{explanation}\n\n"
            share_text += f"Verified on-chain credit passport on QIE Network. "
            share_text += f"Get your credit score at AETHER-SCORE!\n\n"
            share_text += f"#AETHER-SCORE #DeFi #QIE #Blockchain #CreditScore"
            
            # Get badge URL
            badge_url = await self.badge_generator.create_shareable_url(address, badge_data)
            
            # Generate LinkedIn share URL
            linkedin_share_url = f"https://www.linkedin.com/sharing/share-offsite/?{urlencode({'url': badge_url})}"
            
            return {
                "platform": "linkedin",
                "share_text": share_text,
                "badge_url": badge_url,
                "share_url": linkedin_share_url,
                "image_url": badge_url,
            }
        except Exception as e:
            logger.error(f"Error generating LinkedIn share: {e}", exc_info=True)
            return {
                "platform": "linkedin",
                "error": "Failed to generate share",
            }
    
    async def generate_facebook_share(
        self,
        address: str,
        badge_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate Facebook share
        
        Args:
            address: Wallet address
            badge_data: Optional badge data (will fetch if not provided)
            
        Returns:
            Facebook share dict with text, image URL, and share URL
        """
        try:
            if not badge_data:
                badge_data = await self.badge_generator.generate_badge_data(address)
            
            score = badge_data.get("score", 0)
            risk_description = badge_data.get("risk_description", "Unknown")
            
            # Generate share text
            share_text = f"My AETHER-SCORE Credit Score: {score}/1000 ({risk_description}). "
            share_text += f"Verified on-chain credit passport on QIE Network!"
            
            # Get badge URL
            badge_url = await self.badge_generator.create_shareable_url(address, badge_data)
            
            # Generate Facebook share URL
            facebook_share_url = f"https://www.facebook.com/sharer/sharer.php?{urlencode({'u': badge_url})}"
            
            return {
                "platform": "facebook",
                "share_text": share_text,
                "badge_url": badge_url,
                "share_url": facebook_share_url,
                "image_url": badge_url,
            }
        except Exception as e:
            logger.error(f"Error generating Facebook share: {e}", exc_info=True)
            return {
                "platform": "facebook",
                "error": "Failed to generate share",
            }
    
    async def generate_share_links(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Generate all platform share links
        
        Args:
            address: Wallet address
            
        Returns:
            Dict with share links for all platforms
        """
        try:
            # Get badge data once
            badge_data = await self.badge_generator.generate_badge_data(address)
            
            # Generate shares for all platforms
            twitter_share = await self.generate_twitter_share(address, badge_data)
            linkedin_share = await self.generate_linkedin_share(address, badge_data)
            facebook_share = await self.generate_facebook_share(address, badge_data)
            
            return {
                "address": address,
                "badge_data": badge_data,
                "platforms": {
                    "twitter": twitter_share,
                    "linkedin": linkedin_share,
                    "facebook": facebook_share,
                },
            }
        except Exception as e:
            logger.error(f"Error generating share links: {e}", exc_info=True)
            return {
                "address": address,
                "error": "Failed to generate share links",
            }



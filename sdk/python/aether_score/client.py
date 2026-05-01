"""
AETHER-SCORE Python SDK Client
"""
import hmac
import hashlib
import json
from typing import Dict, List, Optional, Any
import requests


class AetherScoreClient:
    """Client for AETHER-SCORE API"""

    def __init__(self, api_key: str, base_url: str = "https://aether-score-backend.onrender.com"):
        """
        Initialize AETHER-SCORE client
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API (default: production URL)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
        })
    
    def get_score(self, address: str) -> Dict[str, Any]:
        """
        Get credit score for an address
        
        Args:
            address: Wallet address
            
        Returns:
            Score response dict
        """
        response = self.session.get(f"{self.base_url}/api/v1/score/{address}")
        response.raise_for_status()
        return response.json()
    
    def get_score_history(self, address: str, limit: int = 30) -> Dict[str, Any]:
        """
        Get score history for an address
        
        Args:
            address: Wallet address
            limit: Maximum number of history entries
            
        Returns:
            Score history response dict
        """
        response = self.session.get(
            f"{self.base_url}/api/v1/score/{address}/history",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def get_loans(self, address: str) -> Dict[str, Any]:
        """
        Get loans for an address
        
        Args:
            address: Wallet address
            
        Returns:
            Loans response dict
        """
        response = self.session.get(f"{self.base_url}/api/v1/loans/{address}")
        response.raise_for_status()
        return response.json()
    
    def get_portfolio(self, address: str) -> Dict[str, Any]:
        """
        Get portfolio data for an address
        
        Args:
            address: Wallet address
            
        Returns:
            Portfolio response dict
        """
        response = self.session.get(f"{self.base_url}/api/v1/portfolio/{address}")
        response.raise_for_status()
        return response.json()
    
    def register_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """
        Register a webhook
        
        Args:
            url: Webhook URL
            events: List of event types to subscribe to
            
        Returns:
            Webhook response dict
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/webhooks",
            json={"url": url, "events": events}
        )
        response.raise_for_status()
        return response.json()
    
    def delete_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """
        Delete a webhook
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            Success response dict
        """
        response = self.session.delete(f"{self.base_url}/api/v1/webhooks/{webhook_id}")
        response.raise_for_status()
        return response.json()
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Webhook payload (JSON string)
            signature: Signature from header
            secret: Webhook secret
            
        Returns:
            True if signature is valid
        """
        try:
            # Parse payload to ensure consistent formatting
            payload_dict = json.loads(payload)
            payload_str = json.dumps(payload_dict, sort_keys=True)
            
            # Generate expected signature
            hmac_obj = hmac.new(
                secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            )
            expected_signature = f"sha256={hmac_obj.hexdigest()}"
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False



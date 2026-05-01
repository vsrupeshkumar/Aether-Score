"""
Nonce management for loan offers to prevent replay attacks
Enhanced with timestamp validation and persistence support
"""
from typing import Dict, Set, Tuple, Optional
import time
import os
import redis
from datetime import datetime, timedelta

class NonceManager:
    """Nonce manager with timestamp validation and optional Redis persistence"""
    
    def __init__(self):
        # In-memory storage (fallback)
        self._used_nonces: Dict[str, Set[Tuple[int, int]]] = {}  # address -> set of (nonce, timestamp)
        self._last_nonce: Dict[str, int] = {}
        
        # Redis connection (optional)
        self.redis_client = None
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis connection failed, using in-memory storage: {e}")
    
    def _get_redis_key(self, address: str, nonce: int) -> str:
        """Get Redis key for nonce"""
        return f"nonce:{address}:{nonce}"
    
    def _get_last_nonce_key(self, address: str) -> str:
        """Get Redis key for last nonce"""
        return f"last_nonce:{address}"
    
    def generate_nonce(self, address: str) -> int:
        """
        Generate a new nonce for an address
        
        Args:
            address: Wallet address
            
        Returns:
            New nonce value
        """
        if self.redis_client:
            try:
                # Use Redis for distributed nonce generation
                key = self._get_last_nonce_key(address)
                nonce = self.redis_client.incr(key)
                if nonce == 1:
                    # Set expiration (24 hours)
                    self.redis_client.expire(key, 86400)
                return nonce
            except Exception:
                pass
        
        # Fallback to in-memory
        if address not in self._last_nonce:
            self._last_nonce[address] = int(time.time())
        else:
            self._last_nonce[address] += 1
        
        return self._last_nonce[address]
    
    def is_nonce_used(self, address: str, nonce: int) -> bool:
        """
        Check if a nonce has been used
        
        Args:
            address: Wallet address
            nonce: Nonce value to check
            
        Returns:
            True if nonce has been used
        """
        if self.redis_client:
            try:
                key = self._get_redis_key(address, nonce)
                return self.redis_client.exists(key) > 0
            except Exception:
                pass
        
        # Fallback to in-memory
        used_nonces = self._used_nonces.get(address, set())
        return any(n == nonce for n, _ in used_nonces)
    
    def mark_nonce_used(self, address: str, nonce: int, timestamp: Optional[int] = None):
        """
        Mark a nonce as used
        
        Args:
            address: Wallet address
            nonce: Nonce value
            timestamp: Timestamp when nonce was used (defaults to current time)
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        if self.redis_client:
            try:
                key = self._get_redis_key(address, nonce)
                # Store with expiration (24 hours)
                self.redis_client.setex(key, 86400, str(timestamp))
                return
            except Exception:
                pass
        
        # Fallback to in-memory
        if address not in self._used_nonces:
            self._used_nonces[address] = set()
        self._used_nonces[address].add((nonce, timestamp))
    
    def validate_nonce_and_timestamp(
        self,
        address: str,
        nonce: int,
        timestamp: int,
        max_age_seconds: int = 300
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate nonce and timestamp to prevent replay attacks
        
        Args:
            address: Wallet address
            nonce: Nonce value
            timestamp: Timestamp from message
            max_age_seconds: Maximum age of message in seconds (default: 5 minutes)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        current_time = int(time.time())
        
        # Check if nonce has been used
        if self.is_nonce_used(address, nonce):
            return False, "Nonce has already been used"
        
        # Check timestamp age
        age = current_time - timestamp
        if age > max_age_seconds:
            return False, f"Message is too old ({age} seconds, max {max_age_seconds})"
        
        # Check for future timestamps (clock skew protection)
        if timestamp > current_time + 60:  # Allow 1 minute clock skew
            return False, "Message timestamp is in the future"
        
        # Mark nonce as used
        self.mark_nonce_used(address, nonce, timestamp)
        
        return True, None
    
    def clear_old_nonces(self, address: str, older_than_seconds: int = 86400):
        """
        Clear nonces older than specified time (for cleanup)
        
        Args:
            address: Wallet address
            older_than_seconds: Age threshold in seconds
        """
        if self.redis_client:
            # Redis handles expiration automatically
            return
        
        # Clean up in-memory storage
        if address in self._used_nonces:
            current_time = int(time.time())
            self._used_nonces[address] = {
                (nonce, ts) for nonce, ts in self._used_nonces[address]
                if current_time - ts < older_than_seconds
            }

# Global instance
nonce_manager = NonceManager()


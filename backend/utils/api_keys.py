"""
API key management
"""
import os
from typing import List, Optional
from utils.secrets_manager import get_secrets_manager

def get_api_keys() -> List[str]:
    """
    Get list of valid API keys from environment
    
    Returns:
        List of API keys
    """
    api_keys_str = os.getenv("API_KEYS", "")
    if not api_keys_str:
        return []
    
    # Split by comma and strip whitespace
    keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
    
    # Decrypt if needed (check if keys are encrypted)
    secrets_manager = get_secrets_manager()
    decrypted_keys = []
    
    for key in keys:
        # Try to decrypt (if it fails, assume it's plaintext)
        try:
            decrypted = secrets_manager.decrypt(key)
            decrypted_keys.append(decrypted)
        except:
            decrypted_keys.append(key)
    
    return decrypted_keys


def validate_api_key(api_key: str) -> bool:
    """
    Validate an API key
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if key is valid
    """
    if not api_key:
        return False
    
    valid_keys = get_api_keys()
    return api_key in valid_keys


def get_api_key_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract API key from Authorization header
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <key>" or "ApiKey <key>")
        
    Returns:
        API key or None
    """
    if not authorization:
        return None
    
    # Support both "Bearer <key>" and "ApiKey <key>" formats
    parts = authorization.split()
    if len(parts) == 2:
        prefix = parts[0].lower()
        if prefix in ["bearer", "apikey", "api-key"]:
            return parts[1]
    
    # If no prefix, assume the whole value is the key
    return authorization.strip()


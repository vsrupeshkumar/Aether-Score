"""
Input sanitization utilities to prevent XSS and injection attacks
"""
import html
import re
from typing import Optional

def sanitize_html(text: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks
    
    Args:
        text: Input text that may contain HTML
        
    Returns:
        Sanitized text with HTML entities escaped
    """
    if not isinstance(text, str):
        return ""
    
    # Escape HTML entities
    sanitized = html.escape(text)
    
    # Remove any remaining script tags (double-check)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def sanitize_chat_message(message: str) -> str:
    """
    Sanitize chat message
    
    Args:
        message: Chat message from user
        
    Returns:
        Sanitized message safe for display
    """
    if not isinstance(message, str):
        return ""
    
    # Remove leading/trailing whitespace
    message = message.strip()
    
    # Remove control characters except newlines and tabs
    message = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', message)
    
    # Limit length (will be validated separately)
    if len(message) > 1000:
        message = message[:1000]
    
    # Basic HTML sanitization (but allow some formatting if needed)
    # For now, just escape HTML
    message = html.escape(message)
    
    return message


def sanitize_address(address: str) -> Optional[str]:
    """
    Sanitize Ethereum address input
    
    Args:
        address: Raw address input
        
    Returns:
        Sanitized address or None if invalid
    """
    if not isinstance(address, str):
        return None
    
    # Remove whitespace
    address = address.strip()
    
    # Remove any non-hex characters (except 0x prefix)
    if address.startswith("0x"):
        address = "0x" + re.sub(r'[^a-fA-F0-9]', '', address[2:])
    else:
        address = re.sub(r'[^a-fA-F0-9]', '', address)
        if address:
            address = "0x" + address
    
    # Check basic format
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address, re.IGNORECASE):
        return None
    
    return address.lower()


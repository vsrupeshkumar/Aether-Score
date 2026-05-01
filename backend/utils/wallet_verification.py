"""
Wallet signature verification
"""
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from typing import Optional
from utils.validators import validate_ethereum_address

def verify_wallet_signature(address: str, message: str, signature: str) -> bool:
    """
    Verify EIP-191 wallet signature
    
    Args:
        address: Ethereum address that signed the message
        message: Original message that was signed
        signature: Hex-encoded signature
        
    Returns:
        True if signature is valid
    """
    try:
        # Validate address format
        checksum_address = validate_ethereum_address(address)
        
        # Validate signature format
        if not signature or not signature.startswith("0x"):
            return False
        
        if len(signature) != 132:  # 0x + 130 hex chars
            return False
        
        # Encode message
        message_encoded = encode_defunct(text=message)
        
        # Recover signer address
        try:
            signer_address = Account.recover_message(message_encoded, signature=signature)
        except Exception:
            return False
        
        # Compare addresses (case-insensitive)
        return signer_address.lower() == checksum_address.lower()
    
    except Exception:
        return False


def create_verification_message(address: str, action: str, timestamp: Optional[int] = None) -> str:
    """
    Create a standard message for wallet signature verification
    
    Args:
        address: User's wallet address
        action: Action being verified (e.g., "generate_score", "create_loan")
        timestamp: Optional timestamp (defaults to current time)
        
    Returns:
        Message string to be signed
    """
    import time
    
    if timestamp is None:
        timestamp = int(time.time())
    
    message = f"""AETHER-SCORE Authentication

Address: {address}
Action: {action}
Timestamp: {timestamp}

By signing this message, you confirm that you own this wallet address and authorize this action."""
    
    return message


def verify_timestamped_message(address: str, message: str, signature: str, max_age_seconds: int = 300) -> bool:
    """
    Verify wallet signature and check message timestamp
    
    Args:
        address: Ethereum address
        message: Signed message (should contain timestamp)
        signature: Hex-encoded signature
        max_age_seconds: Maximum age of message in seconds (default: 5 minutes)
        
    Returns:
        True if signature is valid and message is not expired
    """
    # Verify signature
    if not verify_wallet_signature(address, message, signature):
        return False
    
    # Extract timestamp from message
    import re
    timestamp_match = re.search(r'Timestamp:\s*(\d+)', message)
    if not timestamp_match:
        return False
    
    try:
        timestamp = int(timestamp_match.group(1))
        import time
        current_time = int(time.time())
        
        # Check if message is too old
        if current_time - timestamp > max_age_seconds:
            return False
        
        # Check if message is from the future (clock skew protection)
        if timestamp > current_time + 60:  # Allow 1 minute clock skew
            return False
        
        return True
    except Exception:
        return False



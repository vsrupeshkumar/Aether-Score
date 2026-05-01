"""
Input validation utilities
"""
from web3 import Web3
from typing import Optional
import re

def validate_ethereum_address(address: str) -> str:
    """
    Validate and normalize Ethereum address
    
    Args:
        address: Ethereum address string
        
    Returns:
        Checksummed address
        
    Raises:
        ValueError: If address is invalid
    """
    if not address:
        raise ValueError("Address cannot be empty")
    
    if not isinstance(address, str):
        raise ValueError("Address must be a string")
    
    # Remove whitespace
    address = address.strip()
    
    # Check length (0x + 40 hex chars)
    if len(address) != 42:
        raise ValueError(f"Invalid address length: {len(address)} (expected 42)")
    
    # Check format (starts with 0x)
    if not address.startswith("0x"):
        raise ValueError("Address must start with 0x")
    
    # Check hex characters
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        raise ValueError("Address contains invalid characters")
    
    # Validate checksum
    try:
        checksummed = Web3.to_checksum_address(address)
        return checksummed
    except Exception as e:
        raise ValueError(f"Invalid address checksum: {str(e)}")


def validate_score(score: int) -> int:
    """
    Validate credit score (0-1000)
    
    Args:
        score: Credit score value
        
    Returns:
        Validated score
        
    Raises:
        ValueError: If score is out of range
    """
    if not isinstance(score, int):
        raise ValueError("Score must be an integer")
    
    if score < 0 or score > 1000:
        raise ValueError(f"Score must be between 0 and 1000, got {score}")
    
    return score


def validate_risk_band(risk_band: int) -> int:
    """
    Validate risk band (0-3)
    
    Args:
        risk_band: Risk band value
        
    Returns:
        Validated risk band
        
    Raises:
        ValueError: If risk band is out of range
    """
    if not isinstance(risk_band, int):
        raise ValueError("Risk band must be an integer")
    
    if risk_band < 0 or risk_band > 3:
        raise ValueError(f"Risk band must be between 0 and 3, got {risk_band}")
    
    return risk_band


def validate_message_length(message: str, max_length: int = 1000) -> str:
    """
    Validate message length
    
    Args:
        message: Message string
        max_length: Maximum allowed length
        
    Returns:
        Validated message
        
    Raises:
        ValueError: If message is too long
    """
    if not isinstance(message, str):
        raise ValueError("Message must be a string")
    
    if len(message) > max_length:
        raise ValueError(f"Message exceeds maximum length of {max_length} characters")
    
    if len(message.strip()) == 0:
        raise ValueError("Message cannot be empty")
    
    return message.strip()


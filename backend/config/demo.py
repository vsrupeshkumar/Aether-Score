"""
Demo mode configuration for evaluators

Provides pre-configured demo addresses and optimized flows for quick evaluation.
"""
import os
from typing import Dict, List, Optional, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# Demo mode flag
DEMO_MODE_ENABLED = os.getenv("DEMO_MODE", "false").lower() == "true"

# Pre-configured demo addresses with known scores (for quick evaluation)
DEMO_ADDRESSES = {
    "high_score": {
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  # Example address
        "expected_score": 850,
        "risk_band": 1,
        "description": "High credit score wallet with good history",
    },
    "medium_score": {
        "address": "0x8ba1f109551bD432803012645Hac136c22C177",  # Example address
        "expected_score": 600,
        "risk_band": 2,
        "description": "Medium credit score wallet",
    },
    "low_score": {
        "address": "0x1234567890123456789012345678901234567890",  # Example address
        "expected_score": 350,
        "risk_band": 3,
        "description": "Low credit score wallet",
    },
}

# Demo mode cache (for fast responses)
_demo_cache: Dict[str, Any] = {}


def is_demo_mode() -> bool:
    """Check if demo mode is enabled"""
    return DEMO_MODE_ENABLED


def get_demo_addresses() -> Dict[str, Dict[str, Any]]:
    """
    Get list of demo addresses for quick evaluation
    
    Returns:
        Dict of demo addresses with metadata
    """
    return DEMO_ADDRESSES.copy()


def is_demo_address(address: str) -> bool:
    """
    Check if address is a demo address
    
    Args:
        address: Wallet address to check
        
    Returns:
        True if address is a demo address
    """
    address_lower = address.lower()
    return any(
        demo_addr["address"].lower() == address_lower
        for demo_addr in DEMO_ADDRESSES.values()
    )


def get_demo_score(address: str) -> Optional[Dict[str, Any]]:
    """
    Get cached demo score for address (if in demo mode)
    
    Args:
        address: Wallet address
        
    Returns:
        Demo score data or None
    """
    if not is_demo_mode():
        return None
    
    address_lower = address.lower()
    for demo_addr in DEMO_ADDRESSES.values():
        if demo_addr["address"].lower() == address_lower:
            return {
                "score": demo_addr["expected_score"],
                "riskBand": demo_addr["risk_band"],
                "explanation": f"Demo mode: {demo_addr['description']}",
                "baseScore": demo_addr["expected_score"],
                "stakingBoost": 0,
                "oraclePenalty": 0,
                "stakedAmount": 0,
                "stakingTier": 0,
            }
    
    return None


def should_skip_expensive_operation(operation: str) -> bool:
    """
    Check if expensive operation should be skipped in demo mode
    
    Args:
        operation: Operation name (e.g., "blockchain_update", "oracle_fetch")
        
    Returns:
        True if operation should be skipped
    """
    if not is_demo_mode():
        return False
    
    # Skip expensive operations in demo mode
    skip_operations = [
        "blockchain_update",
        "oracle_fetch",
        "transaction_indexing",
        "fraud_detection",
    ]
    
    return operation in skip_operations


def get_demo_quick_start_guide() -> List[str]:
    """
    Get quick start guide for evaluators
    
    Returns:
        List of guide steps
    """
    return [
        "1. Connect your wallet (or use demo addresses)",
        "2. View your credit score on the dashboard",
        "3. Try the score simulator to see 'what if' scenarios",
        "4. Explore loan offers in the NeuroLend section",
        "5. Check your portfolio and transaction history",
        "6. View analytics and reports",
    ]


__all__ = [
    "is_demo_mode",
    "get_demo_addresses",
    "is_demo_address",
    "get_demo_score",
    "should_skip_expensive_operation",
    "get_demo_quick_start_guide",
]


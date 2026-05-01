"""
Privacy-compliant analytics utilities
"""
import hashlib
from typing import Optional, Dict, Any
from utils.monitoring import set_user_context, add_breadcrumb, capture_message


def anonymize_address(address: str) -> str:
    """
    Anonymize Ethereum address for privacy-compliant tracking
    
    Args:
        address: Ethereum address
        
    Returns:
        Anonymized address (first 8 + last 4 chars)
    """
    if not address or len(address) < 12:
        return "***"
    return f"{address[:8]}...{address[-4:]}"


def hash_address(address: str) -> str:
    """
    Hash address for consistent but anonymous tracking
    
    Args:
        address: Ethereum address
        
    Returns:
        SHA256 hash (first 16 chars)
    """
    return hashlib.sha256(address.encode()).hexdigest()[:16]


def track_feature_usage(
    feature: str,
    address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Track feature usage (privacy-compliant)
    
    Args:
        feature: Feature name (e.g., "score_generation", "loan_creation")
        address: User address (will be anonymized)
        metadata: Additional metadata (no PII)
    """
    # Set user context with anonymized address
    if address:
        set_user_context(id=hash_address(address))
    
    # Add breadcrumb
    add_breadcrumb(
        message=f"Feature used: {feature}",
        category="feature_usage",
        level="info",
        data=metadata or {}
    )


def track_user_flow(
    step: str,
    flow_name: str,
    address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Track user flow progression (privacy-compliant)
    
    Args:
        step: Current step in flow
        flow_name: Flow name (e.g., "score_to_loan")
        address: User address (will be anonymized)
        metadata: Additional metadata
    """
    if address:
        set_user_context(id=hash_address(address))
    
    add_breadcrumb(
        message=f"Flow: {flow_name} - Step: {step}",
        category="user_flow",
        level="info",
        data={
            "flow": flow_name,
            "step": step,
            **(metadata or {})
        }
    )


def track_error_by_segment(
    error_type: str,
    segment: str,
    address: Optional[str] = None
):
    """
    Track errors by user segment (privacy-compliant)
    
    Args:
        error_type: Type of error
        segment: User segment (e.g., "high_score", "new_user")
        address: User address (will be anonymized)
    """
    if address:
        set_user_context(id=hash_address(address))
    
    capture_message(
        f"Error in segment {segment}: {error_type}",
        level="error",
        segment=segment,
        error_type=error_type
    )


def track_performance_by_location(
    endpoint: str,
    duration: float,
    location: Optional[str] = None  # Anonymized location
):
    """
    Track performance by location (anonymized)
    
    Args:
        endpoint: API endpoint
        duration: Request duration
        location: Anonymized location (e.g., "US", "EU")
    """
    add_breadcrumb(
        message=f"Performance: {endpoint}",
        category="performance",
        level="info",
        data={
            "endpoint": endpoint,
            "duration": duration,
            "location": location
        }
    )


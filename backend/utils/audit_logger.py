"""
Structured audit logging
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request
from models.audit import AuditLog

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create file handler for audit logs
import os
log_dir = os.getenv("AUDIT_LOG_DIR", "logs")
os.makedirs(log_dir, exist_ok=True)

file_handler = logging.FileHandler(f"{log_dir}/audit.log")
file_handler.setLevel(logging.INFO)

# JSON formatter for structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        
        # Add extra fields if present
        if hasattr(record, "user_address"):
            log_data["user_address"] = record.user_address
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, "result"):
            log_data["result"] = record.result
        if hasattr(record, "error_message"):
            log_data["error_message"] = record.error_message
        if hasattr(record, "metadata"):
            log_data["metadata"] = record.metadata
        
        return json.dumps(log_data)

file_handler.setFormatter(JSONFormatter())
audit_logger.addHandler(file_handler)

# Also log to console in development
if os.getenv("ENVIRONMENT") != "production":
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    audit_logger.addHandler(console_handler)


def get_client_ip(request: Request) -> Optional[str]:
    """
    Get client IP address from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        IP address or None
    """
    # Check for forwarded IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    if request.client:
        return request.client.host
    
    return None


def log_audit_event(
    request: Request,
    action: str,
    result: str,
    user_address: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event
    
    Args:
        request: FastAPI request object
        action: Action being performed (e.g., "generate_score", "create_loan")
        result: "success" or "failure"
        user_address: User's wallet address (if available)
        error_message: Error message (if result is "failure")
        metadata: Additional metadata to log
    """
    # Get user address from request state if not provided
    if not user_address:
        user_address = getattr(request.state, "user_address", None)
    
    # Get IP address
    ip_address = get_client_ip(request)
    
    # Get endpoint
    endpoint = f"{request.method} {request.url.path}"
    
    # Log with extra fields
    extra = {
        "user_address": user_address,
        "action": action,
        "endpoint": endpoint,
        "ip_address": ip_address,
        "result": result,
    }
    
    if error_message:
        extra["error_message"] = error_message
    
    if metadata:
        extra["metadata"] = metadata
    
    if result == "success":
        audit_logger.info(f"Audit: {action} - {result}", extra=extra)
    else:
        audit_logger.warning(f"Audit: {action} - {result}", extra=extra)


def log_score_generation(request: Request, address: str, score: int, result: str, error: Optional[str] = None):
    """Log score generation event"""
    log_audit_event(
        request=request,
        action="generate_score",
        result=result,
        user_address=address,
        error_message=error,
        metadata={"score": score}
    )


def log_on_chain_update(request: Request, address: str, tx_hash: str, result: str, error: Optional[str] = None):
    """Log on-chain update event"""
    log_audit_event(
        request=request,
        action="update_on_chain",
        result=result,
        user_address=address,
        error_message=error,
        metadata={"tx_hash": tx_hash}
    )


def log_loan_creation(request: Request, address: str, loan_id: Optional[int], result: str, error: Optional[str] = None):
    """Log loan creation event"""
    log_audit_event(
        request=request,
        action="create_loan",
        result=result,
        user_address=address,
        error_message=error,
        metadata={"loan_id": loan_id}
    )


def log_admin_action(request: Request, action: str, result: str, metadata: Optional[Dict] = None):
    """Log admin action"""
    log_audit_event(
        request=request,
        action=f"admin_{action}",
        result=result,
        metadata=metadata
    )


"""
Audit log models
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuditLog(BaseModel):
    """Audit log entry"""
    timestamp: datetime
    user_address: Optional[str]
    action: str
    endpoint: str
    ip_address: Optional[str]
    result: str  # "success" or "failure"
    error_message: Optional[str] = None
    metadata: Optional[dict] = None


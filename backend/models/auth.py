"""
Authentication models
"""
from pydantic import BaseModel, Field
from typing import Optional

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class TokenData(BaseModel):
    """Token payload data"""
    address: Optional[str] = None
    role: Optional[str] = None

class AuthRequest(BaseModel):
    """Authentication request"""
    address: str = Field(..., description="Wallet address")
    signature: str = Field(..., description="EIP-191 signature proving ownership")
    message: str = Field(..., description="Message that was signed")


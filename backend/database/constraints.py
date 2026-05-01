"""
Database constraint definitions and validation
"""
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


# Constraint definitions for reference
CONSTRAINTS = {
    "users": [
        CheckConstraint("wallet_address ~ '^0x[a-fA-F0-9]{40}$'", name="chk_wallet_format"),
    ],
    "loans": [
        CheckConstraint("amount > 0", name="chk_loan_amount"),
        CheckConstraint("interest_rate >= 0 AND interest_rate <= 100", name="chk_interest_rate"),
        CheckConstraint("term_days > 0", name="chk_term_days"),
        CheckConstraint("status IN ('pending', 'active', 'repaid', 'defaulted', 'liquidated')", name="chk_loan_status"),
    ],
    "loan_payments": [
        CheckConstraint("amount > 0", name="chk_payment_amount"),
        CheckConstraint("payment_type IN ('principal', 'interest', 'both')", name="chk_payment_type"),
    ],
    "transactions": [
        CheckConstraint("status IN ('pending', 'success', 'failed') OR status IS NULL", name="chk_tx_status"),
    ],
    "gdpr_requests": [
        CheckConstraint("request_type IN ('deletion', 'export', 'access')", name="chk_gdpr_request_type"),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="chk_gdpr_status"),
    ],
    "data_retention_log": [
        CheckConstraint("status IN ('success', 'failed', 'partial') OR status IS NULL", name="chk_retention_status"),
    ],
}

# Foreign key relationships
FOREIGN_KEYS = {
    "scores": [("wallet_address", "users", "wallet_address")],
    "score_history": [("wallet_address", "scores", "wallet_address")],
    "user_data": [("wallet_address", "users", "wallet_address")],
    "loans": [("wallet_address", "users", "wallet_address")],
    "loan_payments": [("loan_id", "loans", "id")],
    "transactions": [("wallet_address", "users", "wallet_address")],
    "gdpr_requests": [("wallet_address", "users", "wallet_address")],
}

# Unique constraints
UNIQUE_CONSTRAINTS = {
    "transactions": [("tx_hash",)],
    "users": [("wallet_address",)],
    "scores": [("wallet_address",)],
}


def validate_wallet_address(address: str) -> bool:
    """Validate Ethereum wallet address format"""
    import re
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def validate_loan_status(status: str) -> bool:
    """Validate loan status"""
    valid_statuses = ['pending', 'active', 'repaid', 'defaulted', 'liquidated']
    return status in valid_statuses


def validate_payment_type(payment_type: str) -> bool:
    """Validate payment type"""
    valid_types = ['principal', 'interest', 'both']
    return payment_type in valid_types


def validate_gdpr_request_type(request_type: str) -> bool:
    """Validate GDPR request type"""
    valid_types = ['deletion', 'export', 'access']
    return request_type in valid_types


def validate_gdpr_status(status: str) -> bool:
    """Validate GDPR request status"""
    valid_statuses = ['pending', 'processing', 'completed', 'failed']
    return status in valid_statuses


def validate_transaction_status(status: str) -> bool:
    """Validate transaction status"""
    if status is None:
        return True
    valid_statuses = ['pending', 'success', 'failed']
    return status in valid_statuses


def validate_amount(amount: float) -> bool:
    """Validate amount is positive"""
    return amount > 0


def validate_interest_rate(rate: float) -> bool:
    """Validate interest rate is between 0 and 100"""
    return 0 <= rate <= 100


def validate_term_days(days: int) -> bool:
    """Validate term days is positive"""
    return days > 0


"""
Data validation service for ensuring data integrity
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from database.connection import get_db_session
from database.models import (
    User, Score, Loan, Transaction, GDPRRequest
)
from database.constraints import (
    validate_wallet_address, validate_loan_status, validate_payment_type,
    validate_gdpr_request_type, validate_gdpr_status, validate_transaction_status,
    validate_amount, validate_interest_rate, validate_term_days
)
from sqlalchemy import text, inspect
from utils.logger import get_logger

logger = get_logger(__name__)


class DataValidationService:
    """Service for data validation and integrity checks"""
    
    async def validate_user_data(self, user_data: Dict[str, Any]) -> List[str]:
        """Validate user data before creation/update"""
        errors = []
        
        wallet_address = user_data.get("wallet_address")
        if not wallet_address:
            errors.append("wallet_address is required")
        elif not validate_wallet_address(wallet_address):
            errors.append("wallet_address must be a valid Ethereum address")
        
        email = user_data.get("email")
        if email and "@" not in email:
            errors.append("email must be a valid email address")
        
        return errors
    
    async def validate_loan_data(self, loan_data: Dict[str, Any]) -> List[str]:
        """Validate loan data before creation"""
        errors = []
        
        wallet_address = loan_data.get("wallet_address")
        if not wallet_address or not validate_wallet_address(wallet_address):
            errors.append("wallet_address must be a valid Ethereum address")
        
        amount = loan_data.get("amount")
        if amount is None:
            errors.append("amount is required")
        elif not validate_amount(float(amount)):
            errors.append("amount must be greater than 0")
        
        interest_rate = loan_data.get("interest_rate")
        if interest_rate is None:
            errors.append("interest_rate is required")
        elif not validate_interest_rate(float(interest_rate)):
            errors.append("interest_rate must be between 0 and 100")
        
        term_days = loan_data.get("term_days")
        if term_days is None:
            errors.append("term_days is required")
        elif not validate_term_days(int(term_days)):
            errors.append("term_days must be greater than 0")
        
        status = loan_data.get("status", "pending")
        if not validate_loan_status(status):
            errors.append(f"status must be one of: pending, active, repaid, defaulted, liquidated")
        
        return errors
    
    async def validate_transaction_data(self, tx_data: Dict[str, Any]) -> List[str]:
        """Validate transaction data"""
        errors = []
        
        wallet_address = tx_data.get("wallet_address")
        if not wallet_address or not validate_wallet_address(wallet_address):
            errors.append("wallet_address must be a valid Ethereum address")
        
        tx_hash = tx_data.get("tx_hash")
        if not tx_hash:
            errors.append("tx_hash is required")
        elif not tx_hash.startswith("0x") or len(tx_hash) != 66:
            errors.append("tx_hash must be a valid transaction hash (0x + 64 hex chars)")
        
        status = tx_data.get("status")
        if status and not validate_transaction_status(status):
            errors.append("status must be one of: pending, success, failed")
        
        return errors
    
    async def check_foreign_key_integrity(self) -> Dict[str, List[str]]:
        """Check foreign key integrity across all tables"""
        violations = {}
        
        try:
            async with get_db_session() as session:
                # Check scores -> users
                result = await session.execute(text("""
                    SELECT s.wallet_address 
                    FROM scores s 
                    LEFT JOIN users u ON s.wallet_address = u.wallet_address 
                    WHERE u.wallet_address IS NULL
                """))
                orphaned_scores = [row[0] for row in result.fetchall()]
                if orphaned_scores:
                    violations["scores"] = orphaned_scores
                
                # Check loans -> users
                result = await session.execute(text("""
                    SELECT l.id, l.wallet_address 
                    FROM loans l 
                    LEFT JOIN users u ON l.wallet_address = u.wallet_address 
                    WHERE u.wallet_address IS NULL
                """))
                orphaned_loans = [f"{row[0]}:{row[1]}" for row in result.fetchall()]
                if orphaned_loans:
                    violations["loans"] = orphaned_loans
                
                # Check transactions -> users
                result = await session.execute(text("""
                    SELECT t.id, t.wallet_address 
                    FROM transactions t 
                    LEFT JOIN users u ON t.wallet_address = u.wallet_address 
                    WHERE u.wallet_address IS NULL
                """))
                orphaned_transactions = [f"{row[0]}:{row[1]}" for row in result.fetchall()]
                if orphaned_transactions:
                    violations["transactions"] = orphaned_transactions
                
                # Check loan_payments -> loans
                result = await session.execute(text("""
                    SELECT lp.id, lp.loan_id 
                    FROM loan_payments lp 
                    LEFT JOIN loans l ON lp.loan_id = l.id 
                    WHERE l.id IS NULL
                """))
                orphaned_payments = [f"{row[0]}:{row[1]}" for row in result.fetchall()]
                if orphaned_payments:
                    violations["loan_payments"] = orphaned_payments
                
        except Exception as e:
            logger.error(f"Error checking foreign key integrity: {e}", exc_info=True)
            violations["error"] = [str(e)]
        
        return violations
    
    async def check_constraint_violations(self) -> Dict[str, List[str]]:
        """Check for constraint violations"""
        violations = {}
        
        try:
            async with get_db_session() as session:
                # Check loan amount constraints
                result = await session.execute(text("""
                    SELECT id, amount FROM loans WHERE amount <= 0
                """))
                invalid_amounts = [f"{row[0]}:{row[1]}" for row in result.fetchall()]
                if invalid_amounts:
                    violations["loans_invalid_amount"] = invalid_amounts
                
                # Check interest rate constraints
                result = await session.execute(text("""
                    SELECT id, interest_rate FROM loans 
                    WHERE interest_rate < 0 OR interest_rate > 100
                """))
                invalid_rates = [f"{row[0]}:{row[1]}" for row in result.fetchall()]
                if invalid_rates:
                    violations["loans_invalid_interest_rate"] = invalid_rates
                
                # Check loan status constraints
                result = await session.execute(text("""
                    SELECT id, status FROM loans 
                    WHERE status NOT IN ('pending', 'active', 'repaid', 'defaulted', 'liquidated')
                """))
                invalid_statuses = [f"{row[0]}:{row[1]}" for row in result.fetchall()]
                if invalid_statuses:
                    violations["loans_invalid_status"] = invalid_statuses
                
        except Exception as e:
            logger.error(f"Error checking constraints: {e}", exc_info=True)
            violations["error"] = [str(e)]
        
        return violations
    
    async def validate_all_data(self) -> Dict[str, Any]:
        """Run all validation checks"""
        results = {
            "foreign_key_integrity": await self.check_foreign_key_integrity(),
            "constraint_violations": await self.check_constraint_violations(),
            "is_valid": True
        }
        
        # Check if any violations found
        if results["foreign_key_integrity"] or results["constraint_violations"]:
            results["is_valid"] = False
        
        return results


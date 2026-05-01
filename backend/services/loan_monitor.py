"""
Loan Monitoring Service

Monitors loan repayment status and detects defaults.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from database.models import Loan, Transaction
from database.connection import get_db_session
from database.repositories import LoanRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class LoanMonitor:
    """Service for monitoring loan status"""
    
    def __init__(self):
        self.grace_period_days = int(os.getenv("LOAN_GRACE_PERIOD_DAYS", "7"))
        self.liquidation_threshold = float(os.getenv("LOAN_LIQUIDATION_THRESHOLD", "0.8"))  # 80% of collateral value
    
    async def check_loans(self) -> Dict[str, Any]:
        """
        Check all active loans for defaults
        
        Returns:
            Dict with monitoring results
        """
        try:
            async with get_db_session() as session:
                # Get all active loans
                from sqlalchemy import select
                stmt = select(Loan).where(Loan.status == "active")
                result = await session.execute(stmt)
                loans = list(result.scalars().all())
                
                defaults_detected = []
                loans_checked = 0
                
                for loan in loans:
                    loans_checked += 1
                    default_status = await self._check_loan_default(session, loan)
                    
                    if default_status.get("is_defaulted"):
                        defaults_detected.append({
                            "loan_id": loan.id,
                            "wallet_address": loan.wallet_address,
                            "amount": str(loan.amount),
                            "due_date": loan.due_date.isoformat() if loan.due_date else None,
                            "days_overdue": default_status.get("days_overdue", 0),
                        })
                
                return {
                    "status": "success",
                    "loans_checked": loans_checked,
                    "defaults_detected": len(defaults_detected),
                    "defaults": defaults_detected,
                }
                
        except Exception as e:
            logger.error(f"Error checking loans: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def _check_loan_default(self, session: AsyncSession, loan: Loan) -> Dict[str, Any]:
        """Check if a loan is in default"""
        try:
            if not loan.due_date:
                return {"is_defaulted": False}
            
            now = datetime.now(loan.due_date.tzinfo) if loan.due_date.tzinfo else datetime.now()
            days_overdue = (now - loan.due_date).days
            
            # Check if past due date (with grace period)
            if days_overdue > self.grace_period_days:
                # Mark as defaulted
                loan.status = "defaulted"
                await session.commit()
                
                logger.warning(
                    f"Loan {loan.id} marked as defaulted",
                    extra={
                        "loan_id": loan.id,
                        "wallet_address": loan.wallet_address,
                        "days_overdue": days_overdue,
                    }
                )
                
                return {
                    "is_defaulted": True,
                    "days_overdue": days_overdue,
                }
            
            return {"is_defaulted": False, "days_overdue": max(0, days_overdue)}
            
        except Exception as e:
            logger.error(f"Error checking loan default: {e}", exc_info=True)
            return {"is_defaulted": False}
    
    async def get_defaulted_loans(self) -> List[Loan]:
        """Get all defaulted loans"""
        try:
            async with get_db_session() as session:
                from sqlalchemy import select
                stmt = select(Loan).where(Loan.status == "defaulted")
                result = await session.execute(stmt)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting defaulted loans: {e}", exc_info=True)
            return []


"""
Loan Liquidation Service

Handles liquidation of defaulted loans and collateral seizure.
"""

import os
from typing import Dict, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Loan
from database.connection import get_db_session
from database.repositories import LoanRepository
from services.blockchain import BlockchainService
from services.ml_scoring import MLScoringService
from utils.logger import get_logger

logger = get_logger(__name__)


class LoanLiquidationService:
    """Service for liquidating defaulted loans"""
    
    def __init__(self):
        self.blockchain_service = BlockchainService()
        self.scoring_service = MLScoringService()
        self.liquidation_penalty = float(os.getenv("LIQUIDATION_PENALTY", "0.1"))  # 10% penalty
    
    async def liquidate_loan(self, loan_id: int, force: bool = False) -> Dict[str, Any]:
        """
        Liquidate a defaulted loan
        
        Args:
            loan_id: Loan ID to liquidate
            force: Force liquidation even if not defaulted
            
        Returns:
            Liquidation result
        """
        try:
            async with get_db_session() as session:
                # Get loan
                loan = await session.get(Loan, loan_id)
                if not loan:
                    return {
                        "status": "error",
                        "error": "Loan not found",
                    }
                
                # Check if loan can be liquidated
                if loan.status != "defaulted" and not force:
                    return {
                        "status": "error",
                        "error": "Loan is not in default status",
                    }
                
                if loan.status == "liquidated":
                    return {
                        "status": "error",
                        "error": "Loan already liquidated",
                    }
                
                # Calculate liquidation amount
                liquidation_amount = float(loan.amount) * (1 + self.liquidation_penalty)
                
                # In production, this would:
                # 1. Seize collateral from LendingVault contract
                # 2. Transfer collateral to liquidator
                # 3. Update loan status
                # 4. Adjust borrower credit score
                
                # For now, just update status
                loan.status = "liquidated"
                await session.commit()
                
                # Adjust borrower credit score (penalty for default)
                try:
                    score_result = await self.scoring_service.compute_score(loan.wallet_address)
                    current_score = score_result.get("score", 500)
                    
                    # Reduce score by 20% for default
                    new_score = int(current_score * 0.8)
                    risk_band = score_result.get("riskBand", 2)
                    
                    # Update score on blockchain
                    tx_hash = await self.blockchain_service.update_score(
                        loan.wallet_address,
                        new_score,
                        risk_band
                    )
                    
                    logger.info(
                        f"Adjusted credit score after liquidation",
                        extra={
                            "wallet_address": loan.wallet_address,
                            "old_score": current_score,
                            "new_score": new_score,
                            "tx_hash": tx_hash,
                        }
                    )
                    
                except Exception as e:
                    logger.warning(f"Error adjusting credit score: {e}")
                
                logger.info(
                    f"Loan {loan_id} liquidated",
                    extra={
                        "loan_id": loan_id,
                        "wallet_address": loan.wallet_address,
                        "liquidation_amount": liquidation_amount,
                    }
                )
                
                return {
                    "status": "success",
                    "loan_id": loan_id,
                    "liquidation_amount": liquidation_amount,
                    "wallet_address": loan.wallet_address,
                }
                
        except Exception as e:
            logger.error(f"Error liquidating loan: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def batch_liquidate(self, loan_ids: list[int]) -> Dict[str, Any]:
        """Liquidate multiple loans"""
        results = {
            "successful": [],
            "failed": [],
        }
        
        for loan_id in loan_ids:
            result = await self.liquidate_loan(loan_id)
            if result.get("status") == "success":
                results["successful"].append(loan_id)
            else:
                results["failed"].append({
                    "loan_id": loan_id,
                    "error": result.get("error"),
                })
        
        return results


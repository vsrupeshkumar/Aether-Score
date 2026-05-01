"""
Default Handler Service

Orchestrates loan default detection and handling.
"""

import os
from typing import Dict, List, Any
from services.loan_monitor import LoanMonitor
from services.loan_liquidation import LoanLiquidationService
from utils.logger import get_logger

logger = get_logger(__name__)


class DefaultHandler:
    """Service for handling loan defaults"""
    
    def __init__(self):
        self.loan_monitor = LoanMonitor()
        self.liquidation_service = LoanLiquidationService()
        self.auto_liquidate = os.getenv("AUTO_LIQUIDATE", "false").lower() == "true"
    
    async def process_defaults(self) -> Dict[str, Any]:
        """
        Process all loan defaults
        
        Returns:
            Processing results
        """
        try:
            # Check for defaults
            monitoring_result = await self.loan_monitor.check_loans()
            
            defaults_detected = monitoring_result.get("defaults", [])
            
            if not defaults_detected:
                return {
                    "status": "success",
                    "defaults_processed": 0,
                    "message": "No defaults detected",
                }
            
            # Process each default
            processed = []
            liquidated = []
            
            for default_info in defaults_detected:
                loan_id = default_info["loan_id"]
                
                # Auto-liquidate if enabled
                if self.auto_liquidate:
                    liquidation_result = await self.liquidation_service.liquidate_loan(loan_id)
                    
                    if liquidation_result.get("status") == "success":
                        liquidated.append(loan_id)
                        processed.append({
                            "loan_id": loan_id,
                            "action": "liquidated",
                        })
                    else:
                        processed.append({
                            "loan_id": loan_id,
                            "action": "marked_defaulted",
                            "error": liquidation_result.get("error"),
                        })
                else:
                    # Just mark as defaulted (manual liquidation required)
                    processed.append({
                        "loan_id": loan_id,
                        "action": "marked_defaulted",
                    })
            
            logger.info(
                f"Processed {len(processed)} defaults",
                extra={
                    "defaults_processed": len(processed),
                    "liquidated": len(liquidated),
                }
            )
            
            return {
                "status": "success",
                "defaults_processed": len(processed),
                "liquidated": len(liquidated),
                "processed": processed,
            }
            
        except Exception as e:
            logger.error(f"Error processing defaults: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def get_default_summary(self) -> Dict[str, Any]:
        """Get summary of defaulted loans"""
        try:
            defaulted_loans = await self.loan_monitor.get_defaulted_loans()
            
            total_defaulted_amount = sum(float(loan.amount) for loan in defaulted_loans)
            
            return {
                "total_defaulted": len(defaulted_loans),
                "total_amount": total_defaulted_amount,
                "loans": [
                    {
                        "loan_id": loan.id,
                        "wallet_address": loan.wallet_address,
                        "amount": str(loan.amount),
                        "due_date": loan.due_date.isoformat() if loan.due_date else None,
                    }
                    for loan in defaulted_loans
                ],
            }
        except Exception as e:
            logger.error(f"Error getting default summary: {e}", exc_info=True)
            return {
                "total_defaulted": 0,
                "total_amount": 0,
                "error": str(e),
            }


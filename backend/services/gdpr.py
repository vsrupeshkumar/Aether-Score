"""
GDPR compliance service
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from database.connection import get_db_session
from database.models import (
    User, Score, ScoreHistory, UserData, Loan, LoanPayment,
    Transaction, GDPRRequest
)
from database.repositories import (
    UserRepository, GDPRRepository, ScoreRepository,
    ScoreHistoryRepository, TransactionRepository, LoanRepository
)
from utils.logger import get_logger

logger = get_logger(__name__)


class GDPRService:
    """Service for GDPR compliance operations"""
    
    GRACE_PERIOD_DAYS = int(os.getenv("GDPR_DELETION_GRACE_PERIOD_DAYS", "30"))
    
    async def export_user_data(self, wallet_address: str) -> Dict[str, Any]:
        """Export all user data in JSON format"""
        try:
            async with get_db_session() as session:
                # Get user
                user = await UserRepository.get_user(session, wallet_address)
                if not user:
                    return {"error": "User not found"}
                
                # Collect all user data
                data = {
                    "wallet_address": wallet_address,
                    "exported_at": datetime.utcnow().isoformat(),
                    "user": {
                        "email": user.email,
                        "preferences": user.preferences,
                        "gdpr_consent": user.gdpr_consent,
                        "consent_date": user.consent_date.isoformat() if user.consent_date else None,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                    },
                    "scores": [],
                    "score_history": [],
                    "loans": [],
                    "transactions": [],
                }
                
                # Get scores
                score = await ScoreRepository.get_score(session, wallet_address)
                if score:
                    data["scores"].append({
                        "score": score.score,
                        "risk_band": score.risk_band,
                        "last_updated": score.last_updated.isoformat(),
                        "computed_at": score.computed_at.isoformat(),
                    })
                
                # Get score history
                history = await ScoreHistoryRepository.get_history(session, wallet_address, limit=1000)
                data["score_history"] = [{
                    "score": h.score,
                    "risk_band": h.risk_band,
                    "timestamp": h.timestamp.isoformat(),
                } for h in history]
                
                # Get loans
                loans = await LoanRepository.get_loans_by_user(session, wallet_address)
                data["loans"] = [{
                    "loan_id": loan.loan_id,
                    "amount": str(loan.amount),
                    "interest_rate": str(loan.interest_rate),
                    "term_days": loan.term_days,
                    "status": loan.status,
                    "created_at": loan.created_at.isoformat() if loan.created_at else None,
                    "due_date": loan.due_date.isoformat() if loan.due_date else None,
                } for loan in loans]
                
                # Get transactions
                transactions = await TransactionRepository.get_transactions_by_user(session, wallet_address, limit=1000)
                data["transactions"] = [{
                    "tx_hash": tx.tx_hash,
                    "tx_type": tx.tx_type,
                    "block_number": tx.block_number,
                    "block_timestamp": tx.block_timestamp.isoformat() if tx.block_timestamp else None,
                    "value": str(tx.value) if tx.value else None,
                    "status": tx.status,
                } for tx in transactions]
                
                return data
        except Exception as e:
            logger.error(f"Error exporting user data: {e}", exc_info=True, extra={"address": wallet_address})
            return {"error": str(e)}
    
    async def request_deletion(self, wallet_address: str) -> Dict[str, Any]:
        """Request user data deletion"""
        try:
            async with get_db_session() as session:
                # Create GDPR request
                gdpr_request = await GDPRRepository.create_request(
                    session,
                    wallet_address,
                    "deletion"
                )
                
                # Mark user for deletion
                await UserRepository.request_deletion(session, wallet_address)
                
                await session.commit()
                
                logger.info(
                    f"GDPR deletion requested for {wallet_address}",
                    extra={"request_id": gdpr_request.id, "address": wallet_address}
                )
                
                return {
                    "request_id": gdpr_request.id,
                    "status": "pending",
                    "grace_period_days": self.GRACE_PERIOD_DAYS,
                    "message": f"Deletion will be processed after {self.GRACE_PERIOD_DAYS} day grace period"
                }
        except Exception as e:
            logger.error(f"Error requesting deletion: {e}", exc_info=True, extra={"address": wallet_address})
            return {"error": str(e)}
    
    async def process_deletion_requests(self) -> Dict[str, Any]:
        """Process pending deletion requests after grace period"""
        try:
            async with get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=self.GRACE_PERIOD_DAYS)
                
                # Get pending deletion requests past grace period
                from sqlalchemy import select
                result = await session.execute(
                    select(GDPRRequest).where(
                        GDPRRequest.request_type == "deletion",
                        GDPRRequest.status == "pending",
                        GDPRRequest.requested_at < cutoff_date
                    )
                )
                requests = result.scalars().all()
                
                processed = 0
                failed = 0
                
                for req in requests:
                    try:
                        # Update request status
                        await GDPRRepository.update_request_status(
                            session,
                            req.id,
                            "processing"
                        )
                        
                        # Delete user data
                        await self._delete_user_data(session, req.wallet_address)
                        
                        # Mark request as completed
                        await GDPRRepository.update_request_status(
                            session,
                            req.id,
                            "completed"
                        )
                        
                        processed += 1
                        
                        logger.info(
                            f"Processed GDPR deletion for {req.wallet_address}",
                            extra={"request_id": req.id, "address": req.wallet_address}
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing deletion request {req.id}: {e}",
                            exc_info=True
                        )
                        await GDPRRepository.update_request_status(
                            session,
                            req.id,
                            "failed",
                            error_message=str(e)
                        )
                        failed += 1
                
                await session.commit()
                
                return {
                    "processed": processed,
                    "failed": failed,
                    "total": len(requests)
                }
        except Exception as e:
            logger.error(f"Error processing deletion requests: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _delete_user_data(self, session, wallet_address: str):
        """Delete all user data (soft delete)"""
        # Soft delete user
        user = await UserRepository.get_user(session, wallet_address)
        if user:
            user.deleted_at = datetime.utcnow()
        
        # Note: In production, you may want to hard delete or anonymize data
        # For now, we use soft delete to maintain referential integrity
    
    async def request_export(self, wallet_address: str) -> Dict[str, Any]:
        """Request user data export"""
        try:
            async with get_db_session() as session:
                # Create GDPR request
                gdpr_request = await GDPRRepository.create_request(
                    session,
                    wallet_address,
                    "export"
                )
                
                # Generate export
                export_data = await self.export_user_data(wallet_address)
                
                if "error" in export_data:
                    await GDPRRepository.update_request_status(
                        session,
                        gdpr_request.id,
                        "failed",
                        error_message=export_data["error"]
                    )
                    return export_data
                
                # Save export to file (in production, save to S3 or similar)
                export_dir = os.getenv("GDPR_EXPORT_DIR", "/tmp/gdpr_exports")
                os.makedirs(export_dir, exist_ok=True)
                
                export_file = f"{export_dir}/export_{wallet_address}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                with open(export_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                # Update request with file path
                await GDPRRepository.update_request_status(
                    session,
                    gdpr_request.id,
                    "completed",
                    export_file_path=export_file
                )
                
                await session.commit()
                
                return {
                    "request_id": gdpr_request.id,
                    "status": "completed",
                    "export_file": export_file,
                    "data": export_data
                }
        except Exception as e:
            logger.error(f"Error requesting export: {e}", exc_info=True, extra={"address": wallet_address})
            return {"error": str(e)}


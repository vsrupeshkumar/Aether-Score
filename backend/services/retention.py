"""
Data retention policy service
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from database.connection import get_db_session
from database.models import (
    ScoreHistory, Transaction, DataRetentionLog
)
from database.repositories import ScoreHistoryRepository
from sqlalchemy import delete, and_, select, func
from utils.logger import get_logger

logger = get_logger(__name__)


class DataRetentionService:
    """Service for managing data retention policies"""
    
    # Retention periods in days
    RETENTION_PERIODS = {
        "score_history": int(os.getenv("RETENTION_SCORE_HISTORY_DAYS", "365")),  # 1 year
        "transactions": int(os.getenv("RETENTION_TRANSACTIONS_DAYS", "365")),  # 1 year
        "audit_logs": int(os.getenv("RETENTION_AUDIT_LOGS_DAYS", "730")),  # 2 years
    }
    
    async def cleanup_old_score_history(self, archive: bool = True) -> Dict[str, Any]:
        """Clean up old score history records"""
        retention_days = self.RETENTION_PERIODS["score_history"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        try:
            async with get_db_session() as session:
                # Count records to delete
                result = await session.execute(
                    select(func.count(ScoreHistory.id)).where(
                        ScoreHistory.timestamp < cutoff_date
                    )
                )
                count = result.scalar() or 0
                
                if count == 0:
                    return {
                        "table": "score_history",
                        "records_deleted": 0,
                        "archived_count": 0,
                        "status": "success"
                    }
                
                # Archive if enabled
                archived_count = 0
                if archive:
                    archived_count = await self._archive_score_history(session, cutoff_date)
                
                # Delete old records
                result = await session.execute(
                    delete(ScoreHistory).where(ScoreHistory.timestamp < cutoff_date)
                )
                deleted_count = result.rowcount
                
                # Log retention action
                await self._log_retention_action(
                    session,
                    "score_history",
                    deleted_count,
                    archived_count,
                    retention_days,
                    "success" if deleted_count > 0 else "failed"
                )
                
                logger.info(
                    f"Cleaned up {deleted_count} old score history records",
                    extra={
                        "table": "score_history",
                        "deleted": deleted_count,
                        "archived": archived_count,
                        "cutoff_date": cutoff_date.isoformat()
                    }
                )
                
                return {
                    "table": "score_history",
                    "records_deleted": deleted_count,
                    "archived_count": archived_count,
                    "status": "success"
                }
        except Exception as e:
            logger.error(f"Error cleaning up score history: {e}", exc_info=True)
            return {
                "table": "score_history",
                "records_deleted": 0,
                "archived_count": 0,
                "status": "failed",
                "error": str(e)
            }
    
    async def cleanup_old_transactions(self, archive: bool = True) -> Dict[str, Any]:
        """Clean up old transaction records"""
        retention_days = self.RETENTION_PERIODS["transactions"]
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        try:
            async with get_db_session() as session:
                # Count records to delete
                from sqlalchemy import select, func
                result = await session.execute(
                    select(func.count(Transaction.id)).where(
                        Transaction.block_timestamp < cutoff_date
                    )
                )
                count = result.scalar() or 0
                
                if count == 0:
                    return {
                        "table": "transactions",
                        "records_deleted": 0,
                        "archived_count": 0,
                        "status": "success"
                    }
                
                # Archive if enabled
                archived_count = 0
                if archive:
                    archived_count = await self._archive_transactions(session, cutoff_date)
                
                # Delete old records
                result = await session.execute(
                    delete(Transaction).where(Transaction.block_timestamp < cutoff_date)
                )
                deleted_count = result.rowcount
                
                # Log retention action
                await self._log_retention_action(
                    session,
                    "transactions",
                    deleted_count,
                    archived_count,
                    retention_days,
                    "success" if deleted_count > 0 else "failed"
                )
                
                logger.info(
                    f"Cleaned up {deleted_count} old transaction records",
                    extra={
                        "table": "transactions",
                        "deleted": deleted_count,
                        "archived": archived_count,
                        "cutoff_date": cutoff_date.isoformat()
                    }
                )
                
                return {
                    "table": "transactions",
                    "records_deleted": deleted_count,
                    "archived_count": archived_count,
                    "status": "success"
                }
        except Exception as e:
            logger.error(f"Error cleaning up transactions: {e}", exc_info=True)
            return {
                "table": "transactions",
                "records_deleted": 0,
                "archived_count": 0,
                "status": "failed",
                "error": str(e)
            }
    
    async def cleanup_all(self, archive: bool = True) -> Dict[str, Any]:
        """Run cleanup for all tables"""
        results = {}
        
        # Cleanup score history
        results["score_history"] = await self.cleanup_old_score_history(archive)
        
        # Cleanup transactions
        results["transactions"] = await self.cleanup_old_transactions(archive)
        
        return results
    
    async def _archive_score_history(self, session, cutoff_date: datetime) -> int:
        """Archive score history records to cold storage"""
        # This would integrate with S3 or other cold storage
        # For now, return 0 (archival not implemented)
        return 0
    
    async def _archive_transactions(self, session, cutoff_date: datetime) -> int:
        """Archive transaction records to cold storage"""
        # This would integrate with S3 or other cold storage
        # For now, return 0 (archival not implemented)
        return 0
    
    async def _log_retention_action(
        self,
        session,
        table_name: str,
        records_deleted: int,
        archived_count: int,
        retention_period_days: int,
        status: str
    ):
        """Log retention action to data_retention_log table"""
        try:
            log_entry = DataRetentionLog(
                table_name=table_name,
                records_deleted=records_deleted,
                archived_count=archived_count,
                retention_period_days=retention_period_days,
                status=status
            )
            session.add(log_entry)
        except Exception as e:
            logger.error(f"Error logging retention action: {e}", exc_info=True)


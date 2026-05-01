"""
Data archival service for moving old data to cold storage
"""
import os
import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from database.connection import get_db_session
from database.models import ScoreHistory, Transaction
from sqlalchemy import select, func
from utils.logger import get_logger

logger = get_logger(__name__)


class ArchivalService:
    """Service for archiving data to cold storage"""
    
    S3_BUCKET = os.getenv("ARCHIVE_S3_BUCKET")
    S3_REGION = os.getenv("AWS_REGION", "us-east-1")
    ARCHIVE_RETENTION_DAYS = int(os.getenv("ARCHIVE_RETENTION_DAYS", "365"))
    
    def __init__(self):
        self.s3_client = None
        if self.S3_BUCKET:
            try:
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.S3_REGION
                )
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
    
    async def archive_score_history(
        self,
        cutoff_date: datetime,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """Archive score history older than cutoff date"""
        try:
            async with get_db_session() as session:
                # Count records to archive
                result = await session.execute(
                    select(func.count(ScoreHistory.id)).where(
                        ScoreHistory.timestamp < cutoff_date
                    )
                )
                total_count = result.scalar() or 0
                
                if total_count == 0:
                    return {
                        "archived": 0,
                        "status": "success",
                        "message": "No records to archive"
                    }
                
                archived_count = 0
                offset = 0
                
                while offset < total_count:
                    # Fetch batch
                    result = await session.execute(
                        select(ScoreHistory)
                        .where(ScoreHistory.timestamp < cutoff_date)
                        .order_by(ScoreHistory.timestamp)
                        .limit(batch_size)
                        .offset(offset)
                    )
                    records = result.scalars().all()
                    
                    if not records:
                        break
                    
                    # Convert to JSON
                    data = [{
                        "id": r.id,
                        "wallet_address": r.wallet_address,
                        "score": r.score,
                        "risk_band": r.risk_band,
                        "timestamp": r.timestamp.isoformat()
                    } for r in records]
                    
                    # Upload to S3
                    archive_key = f"score_history/{cutoff_date.strftime('%Y/%m')}/batch_{offset}.json"
                    if await self._upload_to_s3(archive_key, data):
                        archived_count += len(records)
                        logger.info(
                            f"Archived {len(records)} score history records",
                            extra={"batch": offset, "total": archived_count}
                        )
                    else:
                        logger.error(f"Failed to archive batch {offset}")
                    
                    offset += batch_size
                
                return {
                    "archived": archived_count,
                    "total": total_count,
                    "status": "success" if archived_count == total_count else "partial"
                }
        except Exception as e:
            logger.error(f"Error archiving score history: {e}", exc_info=True)
            return {
                "archived": 0,
                "status": "failed",
                "error": str(e)
            }
    
    async def archive_transactions(
        self,
        cutoff_date: datetime,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """Archive transactions older than cutoff date"""
        try:
            async with get_db_session() as session:
                # Count records to archive
                result = await session.execute(
                    select(func.count(Transaction.id)).where(
                        Transaction.block_timestamp < cutoff_date
                    )
                )
                total_count = result.scalar() or 0
                
                if total_count == 0:
                    return {
                        "archived": 0,
                        "status": "success",
                        "message": "No records to archive"
                    }
                
                archived_count = 0
                offset = 0
                
                while offset < total_count:
                    # Fetch batch
                    result = await session.execute(
                        select(Transaction)
                        .where(Transaction.block_timestamp < cutoff_date)
                        .order_by(Transaction.block_timestamp)
                        .limit(batch_size)
                        .offset(offset)
                    )
                    records = result.scalars().all()
                    
                    if not records:
                        break
                    
                    # Convert to JSON
                    data = [{
                        "id": r.id,
                        "wallet_address": r.wallet_address,
                        "tx_hash": r.tx_hash,
                        "tx_type": r.tx_type,
                        "block_number": r.block_number,
                        "block_timestamp": r.block_timestamp.isoformat() if r.block_timestamp else None,
                        "from_address": r.from_address,
                        "to_address": r.to_address,
                        "value": str(r.value) if r.value else None,
                        "gas_used": r.gas_used,
                        "gas_price": r.gas_price,
                        "status": r.status,
                        "metadata": r.metadata
                    } for r in records]
                    
                    # Upload to S3
                    archive_key = f"transactions/{cutoff_date.strftime('%Y/%m')}/batch_{offset}.json"
                    if await self._upload_to_s3(archive_key, data):
                        archived_count += len(records)
                        logger.info(
                            f"Archived {len(records)} transaction records",
                            extra={"batch": offset, "total": archived_count}
                        )
                    else:
                        logger.error(f"Failed to archive batch {offset}")
                    
                    offset += batch_size
                
                return {
                    "archived": archived_count,
                    "total": total_count,
                    "status": "success" if archived_count == total_count else "partial"
                }
        except Exception as e:
            logger.error(f"Error archiving transactions: {e}", exc_info=True)
            return {
                "archived": 0,
                "status": "failed",
                "error": str(e)
            }
    
    async def _upload_to_s3(self, key: str, data: List[Dict[str, Any]]) -> bool:
        """Upload data to S3"""
        if not self.s3_client or not self.S3_BUCKET:
            logger.warning("S3 not configured, skipping upload")
            return False
        
        try:
            json_data = json.dumps(data, indent=2)
            self.s3_client.put_object(
                Bucket=self.S3_BUCKET,
                Key=key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json',
                StorageClass='GLACIER'  # Use Glacier for cost savings
            )
            return True
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}", exc_info=True)
            return False
    
    async def restore_from_archive(
        self,
        archive_key: str,
        table_name: str
    ) -> Dict[str, Any]:
        """Restore data from archive"""
        if not self.s3_client or not self.S3_BUCKET:
            return {"error": "S3 not configured"}
        
        try:
            # Download from S3
            response = self.s3_client.get_object(
                Bucket=self.S3_BUCKET,
                Key=archive_key
            )
            data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Note: Actual restore would insert data back into database
            # This is a placeholder - implement based on your needs
            
            return {
                "restored": len(data),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error restoring from archive: {e}", exc_info=True)
            return {
                "restored": 0,
                "status": "failed",
                "error": str(e)
            }


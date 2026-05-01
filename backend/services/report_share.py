"""
Report share manager for managing report sharing with DeFi protocols
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from utils.logger import get_logger
from database.connection import get_session
from database.models import ReportShare, CreditReport
from sqlalchemy import select, desc

logger = get_logger(__name__)


class ReportShareManager:
    """Service for managing report shares"""
    
    def __init__(self):
        pass
    
    async def create_share_link(
        self,
        address: str,
        protocol_address: str,
        report_id: Optional[int] = None,
        expires_in_days: int = 30,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Create shareable link
        
        Args:
            address: Wallet address (owner)
            protocol_address: Protocol address to share with
            report_id: Optional report ID (will create new report if not provided)
            expires_in_days: Days until link expires
            session: Database session (optional)
            
        Returns:
            Share link dict
        """
        try:
            from services.report_exporter import ReportExporter
            
            exporter = ReportExporter()
            
            if report_id:
                # Share existing report
                async with get_session() as db_session:
                    result = await db_session.execute(
                        select(CreditReport).where(
                            CreditReport.id == report_id,
                            CreditReport.wallet_address == address
                        )
                    )
                    report = result.scalar_one_or_none()
                    
                    if not report:
                        return None
                    
                    share_token = exporter.generate_share_token()
                    
                    share = ReportShare(
                        report_id=report_id,
                        wallet_address=address,
                        shared_with_address=protocol_address,
                        share_token=share_token,
                        expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days > 0 else None
                    )
                    db_session.add(share)
                    await db_session.commit()
                    
                    return {
                        "share_id": share.id,
                        "share_token": share_token,
                        "share_url": f"/api/reports/shared/{share_token}",
                        "expires_at": share.expires_at.isoformat() if share.expires_at else None,
                    }
            else:
                # Create new report and share
                return await exporter.share_with_protocol(
                    address,
                    protocol_address,
                    None,
                    expires_in_days,
                    session
                )
        except Exception as e:
            logger.error(f"Error creating share link: {e}", exc_info=True)
            return None
    
    async def get_shared_reports(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get reports shared by user
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of shared report dicts
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._get_shared_reports(address, db_session)
            else:
                return await self._get_shared_reports(address, session)
        except Exception as e:
            logger.error(f"Error getting shared reports: {e}", exc_info=True)
            return []
    
    async def _get_shared_reports(
        self,
        address: str,
        session
    ) -> List[Dict[str, Any]]:
        """Get shared reports from database"""
        try:
            result = await session.execute(
                select(ReportShare, CreditReport)
                .join(CreditReport, ReportShare.report_id == CreditReport.id)
                .where(ReportShare.wallet_address == address)
                .order_by(desc(ReportShare.created_at))
            )
            rows = result.all()
            
            return [
                {
                    "share_id": share.id,
                    "report_id": share.report_id,
                    "shared_with_address": share.shared_with_address,
                    "share_token": share.share_token,
                    "expires_at": share.expires_at.isoformat() if share.expires_at else None,
                    "access_count": share.access_count,
                    "created_at": share.created_at.isoformat() if share.created_at else None,
                    "report": {
                        "report_type": report.report_type,
                        "format": report.format,
                        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
                    } if report else None,
                }
                for share, report in rows
            ]
        except Exception as e:
            logger.error(f"Error in _get_shared_reports: {e}", exc_info=True)
            return []
    
    async def get_received_reports(
        self,
        protocol_address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get reports received by protocol
        
        Args:
            protocol_address: Protocol address
            session: Database session (optional)
            
        Returns:
            List of received report dicts
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._get_received_reports(protocol_address, db_session)
            else:
                return await self._get_received_reports(protocol_address, session)
        except Exception as e:
            logger.error(f"Error getting received reports: {e}", exc_info=True)
            return []
    
    async def _get_received_reports(
        self,
        protocol_address: str,
        session
    ) -> List[Dict[str, Any]]:
        """Get received reports from database"""
        try:
            result = await session.execute(
                select(ReportShare, CreditReport)
                .join(CreditReport, ReportShare.report_id == CreditReport.id)
                .where(ReportShare.shared_with_address == protocol_address)
                .order_by(desc(ReportShare.created_at))
            )
            rows = result.all()
            
            return [
                {
                    "share_id": share.id,
                    "report_id": share.report_id,
                    "wallet_address": share.wallet_address,
                    "share_token": share.share_token,
                    "expires_at": share.expires_at.isoformat() if share.expires_at else None,
                    "access_count": share.access_count,
                    "created_at": share.created_at.isoformat() if share.created_at else None,
                    "report": {
                        "report_type": report.report_type,
                        "format": report.format,
                        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
                    } if report else None,
                }
                for share, report in rows
            ]
        except Exception as e:
            logger.error(f"Error in _get_received_reports: {e}", exc_info=True)
            return []
    
    async def revoke_share(
        self,
        share_id: int,
        address: str,
        session=None
    ) -> bool:
        """
        Revoke shared report access
        
        Args:
            share_id: Share ID
            address: Wallet address (must be owner)
            session: Database session (optional)
            
        Returns:
            True if revoked successfully
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._revoke_share(share_id, address, db_session)
            else:
                return await self._revoke_share(share_id, address, session)
        except Exception as e:
            logger.error(f"Error revoking share: {e}", exc_info=True)
            return False
    
    async def _revoke_share(
        self,
        share_id: int,
        address: str,
        session
    ) -> bool:
        """Revoke share in database"""
        try:
            result = await session.execute(
                select(ReportShare).where(
                    ReportShare.id == share_id,
                    ReportShare.wallet_address == address
                )
            )
            share = result.scalar_one_or_none()
            
            if not share:
                return False
            
            # Delete share
            await session.delete(share)
            await session.commit()
            
            logger.info(f"Revoked share {share_id} for {address}")
            return True
        except Exception as e:
            logger.error(f"Error in _revoke_share: {e}", exc_info=True)
            await session.rollback()
            return False


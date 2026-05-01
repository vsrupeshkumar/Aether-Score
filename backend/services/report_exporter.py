"""
Report exporter service for exporting reports in multiple formats
"""
from typing import Dict, Optional, Any
import secrets
import string
from datetime import datetime, timedelta
from utils.logger import get_logger
from services.report_generator import ReportGenerator

logger = get_logger(__name__)


class ReportExporter:
    """Service for exporting reports"""
    
    SHARE_TOKEN_LENGTH = 32
    
    def __init__(self):
        self.report_generator = ReportGenerator()
    
    async def export_pdf(
        self,
        address: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export PDF report
        
        Args:
            address: Wallet address
            options: Export options
            
        Returns:
            Export result dict
        """
        try:
            report_type = (options or {}).get('report_type', 'full')
            
            result = await self.report_generator.generate_pdf_report(
                address,
                report_type,
                options
            )
            
            return result
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}", exc_info=True)
            return {
                "error": "Failed to export PDF",
                "address": address,
            }
    
    async def export_json(
        self,
        address: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export JSON report
        
        Args:
            address: Wallet address
            options: Export options
            
        Returns:
            JSON report dict
        """
        try:
            report_type = (options or {}).get('report_type', 'full')
            
            result = await self.report_generator.generate_json_report(
                address,
                report_type,
                options
            )
            
            return result
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}", exc_info=True)
            return {
                "error": "Failed to export JSON",
                "address": address,
            }
    
    async def export_csv(
        self,
        address: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export CSV report (simplified data format)
        
        Args:
            address: Wallet address
            options: Export options
            
        Returns:
            CSV report dict
        """
        try:
            import csv
            import io
            
            report_data = await self.report_generator.format_report_data(
                address,
                (options or {}).get('report_type', 'summary'),
                options
            )
            
            # Convert to CSV format
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Section', 'Field', 'Value'])
            
            # Write data
            sections = report_data.get('sections', {})
            for section_name, section_data in sections.items():
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if not isinstance(value, (dict, list)):
                            writer.writerow([section_name, key, str(value)])
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                "address": address,
                "format": "csv",
                "content": csv_content,
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}", exc_info=True)
            return {
                "error": "Failed to export CSV",
                "address": address,
            }
    
    async def share_with_protocol(
        self,
        address: str,
        protocol_address: str,
        report_data: Optional[Dict[str, Any]] = None,
        expires_in_days: int = 30,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Share report with DeFi protocol
        
        Args:
            address: Wallet address (owner)
            protocol_address: Protocol address to share with
            report_data: Optional report data (will generate if not provided)
            expires_in_days: Days until share expires
            session: Database session (optional)
            
        Returns:
            Share result dict
        """
        try:
            from database.connection import get_session
            
            if session is None:
                async with get_session() as db_session:
                    return await self._share_with_protocol(
                        address, protocol_address, report_data, expires_in_days, db_session
                    )
            else:
                return await self._share_with_protocol(
                    address, protocol_address, report_data, expires_in_days, session
                )
        except Exception as e:
            logger.error(f"Error sharing report: {e}", exc_info=True)
            return None
    
    async def _share_with_protocol(
        self,
        address: str,
        protocol_address: str,
        report_data: Optional[Dict[str, Any]],
        expires_in_days: int,
        session
    ) -> Optional[Dict[str, Any]]:
        """Share report in database"""
        from database.models import CreditReport, ReportShare
        
        try:
            # Generate report if not provided
            if not report_data:
                report_data = await self.report_generator.format_report_data(address)
            
            # Create report record
            report = CreditReport(
                wallet_address=address,
                report_type='full',
                format='json',
                metadata=report_data
            )
            session.add(report)
            await session.flush()
            
            # Generate share token
            share_token = self.generate_share_token()
            
            # Create share record
            share = ReportShare(
                report_id=report.id,
                wallet_address=address,
                shared_with_address=protocol_address,
                share_token=share_token,
                expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days > 0 else None
            )
            session.add(share)
            await session.commit()
            
            logger.info(f"Shared report {report.id} with protocol {protocol_address}")
            
            return {
                "share_id": share.id,
                "report_id": report.id,
                "share_token": share_token,
                "share_url": f"/api/reports/shared/{share_token}",
                "expires_at": share.expires_at.isoformat() if share.expires_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _share_with_protocol: {e}", exc_info=True)
            await session.rollback()
            return None
    
    def generate_share_token(self) -> str:
        """
        Generate secure share token
        
        Returns:
            Secure token string
        """
        return secrets.token_urlsafe(self.SHARE_TOKEN_LENGTH)
    
    async def validate_share_token(
        self,
        token: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Validate share token
        
        Args:
            token: Share token
            session: Database session (optional)
            
        Returns:
            Share info dict if valid, None otherwise
        """
        try:
            from database.connection import get_session
            from database.models import ReportShare, CreditReport
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._validate_share_token(token, db_session)
            else:
                return await self._validate_share_token(token, session)
        except Exception as e:
            logger.error(f"Error validating share token: {e}", exc_info=True)
            return None
    
    async def _validate_share_token(
        self,
        token: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Validate token from database"""
        from database.models import ReportShare, CreditReport
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(ReportShare).where(ReportShare.share_token == token)
            )
            share = result.scalar_one_or_none()
            
            if not share:
                return None
            
            # Check if expired
            if share.expires_at and share.expires_at < datetime.utcnow():
                return None
            
            # Update access info
            share.access_count += 1
            share.accessed_at = datetime.utcnow()
            await session.commit()
            
            # Get report
            report_result = await session.execute(
                select(CreditReport).where(CreditReport.id == share.report_id)
            )
            report = report_result.scalar_one_or_none()
            
            return {
                "share_id": share.id,
                "report_id": share.report_id,
                "wallet_address": share.wallet_address,
                "shared_with_address": share.shared_with_address,
                "expires_at": share.expires_at.isoformat() if share.expires_at else None,
                "access_count": share.access_count,
                "report": {
                    "address": report.wallet_address if report else None,
                    "metadata": report.extra_metadata if report else None,
                } if report else None,
            }
        except Exception as e:
            logger.error(f"Error in _validate_share_token: {e}", exc_info=True)
            await session.rollback()
            return None


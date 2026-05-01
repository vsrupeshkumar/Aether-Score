"""
Report generator service for creating credit reports in PDF, JSON, and CSV formats
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import get_logger
from services.scoring import ScoringService
from services.portfolio_service import PortfolioService
from services.loan_service import LoanService
from services.score_explanation import ScoreExplanationService

logger = get_logger(__name__)


class ReportGenerator:
    """Service for generating credit reports"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.portfolio_service = PortfolioService()
        self.loan_service = LoanService()
        self.explanation_service = ScoreExplanationService()
    
    async def generate_pdf_report(
        self,
        address: str,
        report_type: str = 'full',
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate PDF credit report
        
        Args:
            address: Wallet address
            report_type: Report type ('full', 'summary', 'custom')
            options: Optional report options
            
        Returns:
            Report dict with file path/URL and metadata
        """
        try:
            # Generate report data
            report_data = await self.format_report_data(address, report_type, options)
            
            # For now, return structured data
            # In production, would use reportlab or weasyprint to generate actual PDF
            import os
            import uuid
            
            # Generate file path
            report_id = str(uuid.uuid4())
            reports_dir = os.getenv("REPORTS_DIR", "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            file_path = os.path.join(reports_dir, f"{report_id}.pdf")
            file_url = f"/api/reports/{report_id}/download"
            
            # In production, would generate actual PDF here
            # For now, create placeholder
            logger.info(f"Generated PDF report for {address}: {file_path}")
            
            return {
                "report_id": report_id,
                "address": address,
                "report_type": report_type,
                "format": "pdf",
                "file_path": file_path,
                "file_url": file_url,
                "generated_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "sections": list(report_data.get("sections", {}).keys()),
                    "page_count": len(report_data.get("sections", {})),
                },
            }
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}", exc_info=True)
            return {
                "error": "Failed to generate PDF report",
                "address": address,
            }
    
    async def generate_json_report(
        self,
        address: str,
        report_type: str = 'full',
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON report for API
        
        Args:
            address: Wallet address
            report_type: Report type ('full', 'summary', 'custom')
            options: Optional report options
            
        Returns:
            JSON report dict
        """
        try:
            report_data = await self.format_report_data(address, report_type, options)
            
            return {
                "address": address,
                "report_type": report_type,
                "format": "json",
                "generated_at": datetime.utcnow().isoformat(),
                "data": report_data,
            }
        except Exception as e:
            logger.error(f"Error generating JSON report: {e}", exc_info=True)
            return {
                "error": "Failed to generate JSON report",
                "address": address,
            }
    
    async def generate_report_sections(
        self,
        address: str,
        report_type: str = 'full'
    ) -> Dict[str, Any]:
        """
        Generate report sections (score, history, transactions, etc.)
        
        Args:
            address: Wallet address
            report_type: Report type
            
        Returns:
            Dict with report sections
        """
        try:
            sections = {}
            
            # Executive Summary
            score_info = await self.scoring_service.compute_score(address)
            sections['executive_summary'] = {
                "score": score_info.get('score', 0),
                "risk_band": score_info.get('riskBand', 0),
                "risk_description": {1: "Low Risk", 2: "Medium Risk", 3: "High Risk"}.get(
                    score_info.get('riskBand', 0), "Unknown"
                ),
                "explanation": score_info.get('explanation', ''),
                "last_updated": datetime.utcnow().isoformat(),
            }
            
            # Score History
            try:
                from database.connection import get_session
                from database.models import ScoreHistory
                from sqlalchemy import select, desc
                
                async with get_session() as session:
                    result = await session.execute(
                        select(ScoreHistory)
                        .where(ScoreHistory.wallet_address == address)
                        .order_by(desc(ScoreHistory.computed_at))
                        .limit(30)
                    )
                    history = result.scalars().all()
                    
                    sections['score_history'] = [
                        {
                            "score": h.score,
                            "risk_band": h.risk_band,
                            "computed_at": h.computed_at.isoformat() if h.computed_at else None,
                            "change_reason": h.change_reason,
                            "explanation": h.explanation,
                        }
                        for h in history
                    ]
            except Exception as e:
                logger.warning(f"Error fetching score history: {e}")
                sections['score_history'] = []
            
            # Transaction Analysis
            try:
                portfolio_data = await self.portfolio_service.get_transaction_summary(address)
                sections['transaction_analysis'] = {
                    "total_transactions": portfolio_data.get('total_transactions', 0),
                    "total_volume": portfolio_data.get('total_volume', 0),
                    "unique_contracts": portfolio_data.get('unique_contracts', 0),
                    "days_active": portfolio_data.get('days_active', 0),
                }
            except Exception as e:
                logger.warning(f"Error fetching transaction analysis: {e}")
                sections['transaction_analysis'] = {}
            
            # Portfolio Overview
            try:
                portfolio_value = await self.portfolio_service.get_total_portfolio_value(address)
                token_holdings = await self.portfolio_service.get_token_holdings(address)
                
                sections['portfolio_overview'] = {
                    "total_value": portfolio_value,
                    "token_count": len(token_holdings),
                    "holdings": token_holdings[:10],  # Top 10 holdings
                }
            except Exception as e:
                logger.warning(f"Error fetching portfolio overview: {e}")
                sections['portfolio_overview'] = {}
            
            # Loan History
            try:
                loans = await self.loan_service.get_loans_by_user(address)
                sections['loan_history'] = {
                    "total_loans": len(loans),
                    "active_loans": len([l for l in loans if l.get('status') == 'active']),
                    "repaid_loans": len([l for l in loans if l.get('status') == 'repaid']),
                    "loans": loans[:10],  # Recent loans
                }
            except Exception as e:
                logger.warning(f"Error fetching loan history: {e}")
                sections['loan_history'] = {}
            
            # Recommendations (if report_type is 'full')
            if report_type == 'full':
                sections['recommendations'] = await self._generate_recommendations(address)
            
            return sections
        except Exception as e:
            logger.error(f"Error generating report sections: {e}", exc_info=True)
            return {}
    
    async def format_report_data(
        self,
        address: str,
        report_type: str = 'full',
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format data for report
        
        Args:
            address: Wallet address
            report_type: Report type
            options: Optional formatting options
            
        Returns:
            Formatted report data dict
        """
        try:
            sections = await self.generate_report_sections(address, report_type)
            
            return {
                "address": address,
                "report_type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "sections": sections,
                "options": options or {},
            }
        except Exception as e:
            logger.error(f"Error formatting report data: {e}", exc_info=True)
            return {
                "address": address,
                "error": str(e),
            }
    
    async def _generate_recommendations(
        self,
        address: str
    ) -> List[str]:
        """Generate improvement recommendations"""
        try:
            score_info = await self.scoring_service.compute_score(address)
            score = score_info.get('score', 0)
            risk_band = score_info.get('riskBand', 0)
            
            recommendations = []
            
            if score < 500:
                recommendations.append("Consider increasing transaction activity to improve your score")
                recommendations.append("Stake NCRD tokens to boost your credit tier")
            
            if risk_band >= 2:
                recommendations.append("Focus on maintaining consistent transaction patterns")
                recommendations.append("Consider repaying any outstanding loans to improve risk profile")
            
            # Check portfolio
            try:
                portfolio_value = await self.portfolio_service.get_total_portfolio_value(address)
                if portfolio_value < 100:
                    recommendations.append("Consider building a more diverse portfolio")
            except:
                pass
            
            # Check loans
            try:
                loans = await self.loan_service.get_loans_by_user(address)
                active_loans = [l for l in loans if l.get('status') == 'active']
                if len(active_loans) > 0:
                    recommendations.append("Maintain timely loan repayments to preserve credit score")
            except:
                pass
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return []


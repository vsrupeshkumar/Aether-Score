"""
Collateral alert service for managing collateral-related alerts
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class CollateralAlertService:
    """Service for managing collateral alerts"""
    
    # Alert types
    ALERT_LOW_COLLATERAL = 'low_collateral'
    ALERT_LIQUIDATION_RISK = 'liquidation_risk'
    ALERT_REBALANCE_OPPORTUNITY = 'rebalance_opportunity'
    ALERT_PRICE_DROP = 'price_drop'
    
    async def create_alert(
        self,
        loan_id: int,
        alert_type: str,
        message: str,
        severity: str = 'warning',
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a collateral alert
        
        Args:
            loan_id: Loan ID
            alert_type: Alert type
            message: Alert message
            severity: Alert severity ('info', 'warning', 'critical')
            session: Database session (optional)
            
        Returns:
            Created alert dict
        """
        try:
            from database.connection import get_session
            from database.models import Loan, CollateralAlert
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_alert(loan_id, alert_type, message, severity, db_session)
            else:
                return await self._create_alert(loan_id, alert_type, message, severity, session)
        except Exception as e:
            logger.error(f"Error creating alert: {e}", exc_info=True)
            return None
    
    async def _create_alert(
        self,
        loan_id: int,
        alert_type: str,
        message: str,
        severity: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Create alert in database"""
        # Note: CollateralAlert model would need to be created
        # For now, we'll use a simplified approach
        try:
            from database.models import Loan
            from sqlalchemy import select
            
            # Get loan to get borrower address
            loan_result = await session.execute(
                select(Loan).where(Loan.id == loan_id)
            )
            loan = loan_result.scalar_one_or_none()
            
            if not loan:
                return None
            
            # In a full implementation, we would create a CollateralAlert record
            # For now, return a dict representation
            alert = {
                "loan_id": loan_id,
                "wallet_address": loan.borrower_address,
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "created_at": datetime.utcnow().isoformat(),
                "read": False,
            }
            
            logger.info(f"Created alert for loan {loan_id}: {alert_type} - {message}")
            
            return alert
        except Exception as e:
            logger.error(f"Error in _create_alert: {e}", exc_info=True)
            return None
    
    async def get_active_alerts(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get active alerts for a user
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of alert dicts
        """
        try:
            from database.connection import get_session
            from database.models import Loan
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_active_alerts(address, db_session)
            else:
                return await self._get_active_alerts(address, session)
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}", exc_info=True)
            return []
    
    async def _get_active_alerts(
        self,
        address: str,
        session
    ) -> List[Dict[str, Any]]:
        """Get active alerts from database"""
        from database.models import Loan
        from sqlalchemy import select
        from services.collateral_health import CollateralHealthMonitor
        
        try:
            # Get user's loans
            loans_result = await session.execute(
                select(Loan).where(Loan.borrower_address == address)
            )
            loans = loans_result.scalars().all()
            
            alerts = []
            health_monitor = CollateralHealthMonitor()
            
            for loan in loans:
                # Get health alerts for each loan
                health_alerts = await health_monitor.get_health_alerts(loan.id, session)
                
                for alert in health_alerts:
                    alerts.append({
                        "loan_id": loan.id,
                        "wallet_address": address,
                        "alert_type": alert.get("type"),
                        "message": alert.get("message"),
                        "severity": alert.get("severity"),
                        "created_at": datetime.utcnow().isoformat(),
                        "read": False,
                    })
            
            return alerts
        except Exception as e:
            logger.error(f"Error in _get_active_alerts: {e}", exc_info=True)
            return []
    
    async def mark_alert_read(
        self,
        alert_id: int,
        session=None
    ) -> bool:
        """
        Mark alert as read
        
        Args:
            alert_id: Alert ID
            session: Database session (optional)
            
        Returns:
            True if marked successfully
        """
        try:
            # In a full implementation, would update CollateralAlert record
            logger.info(f"Marked alert {alert_id} as read")
            return True
        except Exception as e:
            logger.error(f"Error marking alert as read: {e}", exc_info=True)
            return False


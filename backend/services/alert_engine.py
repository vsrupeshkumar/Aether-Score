"""
Alert engine service for managing alerts
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class AlertEngine:
    """Service for managing alerts"""
    
    async def create_alert(
        self,
        address: str,
        alert_type: str,
        severity: str,
        message: str,
        suggested_actions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an alert
        
        Args:
            address: Wallet address
            alert_type: Alert type
            severity: Alert severity ('info', 'warning', 'critical')
            message: Alert message
            suggested_actions: List of suggested actions
            metadata: Additional metadata
            session: Database session (optional)
            
        Returns:
            Created alert dict
        """
        try:
            from database.connection import get_session
            from database.models import Alert
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_alert(
                        address, alert_type, severity, message,
                        suggested_actions, metadata, db_session
                    )
            else:
                return await self._create_alert(
                    address, alert_type, severity, message,
                    suggested_actions, metadata, session
                )
        except Exception as e:
            logger.error(f"Error creating alert: {e}", exc_info=True)
            return None
    
    async def _create_alert(
        self,
        address: str,
        alert_type: str,
        severity: str,
        message: str,
        suggested_actions: Optional[List[str]],
        metadata: Optional[Dict[str, Any]],
        session
    ) -> Optional[Dict[str, Any]]:
        """Create alert in database"""
        from database.models import Alert
        
        try:
            alert = Alert(
                wallet_address=address,
                alert_type=alert_type,
                severity=severity,
                message=message,
                suggested_actions=suggested_actions or [],
                read=False,
                dismissed=False
            )
            session.add(alert)
            await session.commit()
            
            logger.info(f"Created alert {alert.id} for {address}: {alert_type}")
            
            return {
                "id": alert.id,
                "wallet_address": address,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "suggested_actions": suggested_actions or [],
                "read": False,
                "dismissed": False,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _create_alert: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def get_active_alerts(
        self,
        address: str,
        include_read: bool = False,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get user's active alerts
        
        Args:
            address: Wallet address
            include_read: Whether to include read alerts
            session: Database session (optional)
            
        Returns:
            List of alert dicts
        """
        try:
            from database.connection import get_session
            from database.models import Alert
            from sqlalchemy import select, and_
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_active_alerts(address, include_read, db_session)
            else:
                return await self._get_active_alerts(address, include_read, session)
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}", exc_info=True)
            return []
    
    async def _get_active_alerts(
        self,
        address: str,
        include_read: bool,
        session
    ) -> List[Dict[str, Any]]:
        """Get active alerts from database"""
        from database.models import Alert
        from sqlalchemy import select, and_
        
        try:
            query = select(Alert).where(
                Alert.wallet_address == address,
                Alert.dismissed == False
            )
            
            if not include_read:
                query = query.where(Alert.read == False)
            
            query = query.order_by(Alert.created_at.desc())
            
            result = await session.execute(query)
            alerts = result.scalars().all()
            
            return [
                {
                    "id": alert.id,
                    "wallet_address": alert.wallet_address,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "suggested_actions": alert.suggested_actions or [],
                    "read": alert.read,
                    "dismissed": alert.dismissed,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                    "read_at": alert.read_at.isoformat() if alert.read_at else None,
                }
                for alert in alerts
            ]
        except Exception as e:
            logger.error(f"Error in _get_active_alerts: {e}", exc_info=True)
            return []
    
    async def mark_alert_read(
        self,
        alert_id: int,
        address: str,
        session=None
    ) -> bool:
        """
        Mark alert as read
        
        Args:
            alert_id: Alert ID
            address: Wallet address (for authorization)
            session: Database session (optional)
            
        Returns:
            True if marked successfully
        """
        try:
            from database.connection import get_session
            from database.models import Alert
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._mark_alert_read(alert_id, address, db_session)
            else:
                return await self._mark_alert_read(alert_id, address, session)
        except Exception as e:
            logger.error(f"Error marking alert as read: {e}", exc_info=True)
            return False
    
    async def _mark_alert_read(
        self,
        alert_id: int,
        address: str,
        session
    ) -> bool:
        """Mark alert as read in database"""
        from database.models import Alert
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(Alert).where(
                    Alert.id == alert_id,
                    Alert.wallet_address == address
                )
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                return False
            
            alert.read = True
            alert.read_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Marked alert {alert_id} as read")
            return True
        except Exception as e:
            logger.error(f"Error in _mark_alert_read: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def dismiss_alert(
        self,
        alert_id: int,
        address: str,
        session=None
    ) -> bool:
        """
        Dismiss alert
        
        Args:
            alert_id: Alert ID
            address: Wallet address (for authorization)
            session: Database session (optional)
            
        Returns:
            True if dismissed successfully
        """
        try:
            from database.connection import get_session
            from database.models import Alert
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._dismiss_alert(alert_id, address, db_session)
            else:
                return await self._dismiss_alert(alert_id, address, session)
        except Exception as e:
            logger.error(f"Error dismissing alert: {e}", exc_info=True)
            return False
    
    async def _dismiss_alert(
        self,
        alert_id: int,
        address: str,
        session
    ) -> bool:
        """Dismiss alert in database"""
        from database.models import Alert
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(Alert).where(
                    Alert.id == alert_id,
                    Alert.wallet_address == address
                )
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                return False
            
            alert.dismissed = True
            alert.dismissed_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Dismissed alert {alert_id}")
            return True
        except Exception as e:
            logger.error(f"Error in _dismiss_alert: {e}", exc_info=True)
            await session.rollback()
            return False


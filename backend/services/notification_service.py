"""
Notification service for multi-channel notifications (in-app, email, push, SMS)
"""
from typing import Dict, List, Optional, Any
from utils.logger import get_logger
from services.alert_engine import AlertEngine
from services.email_service import EmailService
from services.sms_service import SMSService
from services.push_notification import PushNotificationService

logger = get_logger(__name__)


class NotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self):
        self.alert_engine = AlertEngine()
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.push_service = PushNotificationService()
    
    async def send_in_app_notification(
        self,
        address: str,
        alert: Dict[str, Any],
        session=None
    ) -> bool:
        """
        Send in-app notification (stored in database)
        
        Args:
            address: Wallet address
            alert: Alert dict
            session: Database session (optional)
            
        Returns:
            True if sent successfully
        """
        try:
            # Create alert in database (this is the in-app notification)
            created_alert = await self.alert_engine.create_alert(
                address,
                alert.get('alert_type', 'info'),
                alert.get('severity', 'info'),
                alert.get('message', ''),
                alert.get('suggested_actions', []),
                alert.get('metadata', {}),
                session
            )
            
            return created_alert is not None
        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}", exc_info=True)
            return False
    
    async def send_email_notification(
        self,
        address: str,
        alert: Dict[str, Any],
        session=None
    ) -> bool:
        """
        Send email notification
        
        Args:
            address: Wallet address
            alert: Alert dict
            session: Database session (optional)
            
        Returns:
            True if sent successfully
        """
        try:
            # Get notification preferences
            prefs = await self._get_notification_preferences(address, session)
            
            if not prefs or not prefs.get('email_enabled', False):
                logger.debug(f"Email notifications disabled for {address}")
                return False
            
            email_address = prefs.get('email_address')
            if not email_address:
                logger.warning(f"No email address configured for {address}")
                return False
            
            # Send email using email service
            subject = f"AETHER-SCORE Alert: {alert.get('alert_type', 'Alert')}"
            body = self._format_email_body(alert)
            
            return await self.email_service.send_email(
                email_address,
                subject,
                body,
                body  # Use same body for HTML (can be enhanced later)
            )
        except Exception as e:
            logger.error(f"Error sending email notification: {e}", exc_info=True)
            return False
    
    async def send_push_notification(
        self,
        address: str,
        alert: Dict[str, Any],
        session=None
    ) -> bool:
        """
        Send push notification (mobile/web)
        
        Args:
            address: Wallet address
            alert: Alert dict
            session: Database session (optional)
            
        Returns:
            True if sent successfully
        """
        try:
            # Get notification preferences
            prefs = await self._get_notification_preferences(address, session)
            
            if not prefs or not prefs.get('push_enabled', False):
                logger.debug(f"Push notifications disabled for {address}")
                return False
            
            # Send push notification using push service
            title = f"AETHER-SCORE Alert: {alert.get('alert_type', 'Alert')}"
            body = alert.get('message', '')
            data = alert.get('metadata', {})
            
            return await self.push_service.send_push_notification(
                address,
                title,
                body,
                data,
                session
            )
        except Exception as e:
            logger.error(f"Error sending push notification: {e}", exc_info=True)
            return False
    
    async def send_sms_notification(
        self,
        address: str,
        alert: Dict[str, Any],
        session=None
    ) -> bool:
        """
        Send SMS notification
        
        Args:
            address: Wallet address
            alert: Alert dict
            session: Database session (optional)
            
        Returns:
            True if sent successfully
        """
        try:
            # Get notification preferences
            prefs = await self._get_notification_preferences(address, session)
            
            if not prefs or not prefs.get('sms_enabled', False):
                logger.debug(f"SMS notifications disabled for {address}")
                return False
            
            phone_number = prefs.get('phone_number')
            if not phone_number:
                logger.warning(f"No phone number configured for {address}")
                return False
            
            # Send SMS using SMS service
            message = f"AETHER-SCORE: {alert.get('alert_type', 'Alert')} - {alert.get('message', '')}"
            
            return await self.sms_service.send_sms(phone_number, message)
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}", exc_info=True)
            return False
    
    async def send_notification(
        self,
        address: str,
        alert: Dict[str, Any],
        channels: Optional[List[str]] = None,
        session=None
    ) -> Dict[str, bool]:
        """
        Send notification via multiple channels
        
        Args:
            address: Wallet address
            alert: Alert dict
            channels: List of channels ('in_app', 'email', 'push'). If None, uses user preferences
            session: Database session (optional)
            
        Returns:
            Dict with channel -> success status
        """
        try:
            # Get notification preferences if channels not specified
            if channels is None:
                prefs = await self._get_notification_preferences(address, session)
                channels = []
                if prefs.get('in_app_enabled', True):
                    channels.append('in_app')
            if prefs.get('email_enabled', False):
                channels.append('email')
            if prefs.get('push_enabled', False):
                channels.append('push')
            if prefs.get('sms_enabled', False):
                channels.append('sms')
            
            results = {}
            
            # Send via each channel
            if 'in_app' in channels:
                results['in_app'] = await self.send_in_app_notification(address, alert, session)
            
            if 'email' in channels:
                results['email'] = await self.send_email_notification(address, alert, session)
            
            if 'push' in channels:
                results['push'] = await self.send_push_notification(address, alert, session)
            
            if 'sms' in channels:
                results['sms'] = await self.send_sms_notification(address, alert, session)
            
            return results
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
            return {}
    
    async def _get_notification_preferences(
        self,
        address: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """Get notification preferences for user"""
        try:
            from database.connection import get_session
            from database.models import NotificationPreference
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_prefs(address, db_session)
            else:
                return await self._get_prefs(address, session)
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}", exc_info=True)
            return None
    
    async def _get_prefs(
        self,
        address: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Get preferences from database"""
        from database.models import NotificationPreference
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(NotificationPreference).where(NotificationPreference.wallet_address == address)
            )
            prefs = result.scalar_one_or_none()
            
            if not prefs:
                # Return defaults
                return {
                    "wallet_address": address,
                    "in_app_enabled": True,
                    "email_enabled": False,
                    "push_enabled": False,
                    "sms_enabled": False,
                    "email_address": None,
                    "phone_number": None,
                }
            
            return {
                "wallet_address": address,
                "in_app_enabled": prefs.in_app_enabled,
                "email_enabled": prefs.email_enabled,
                "push_enabled": prefs.push_enabled,
                "sms_enabled": getattr(prefs, 'sms_enabled', False),
                "email_address": prefs.email_address,
                "phone_number": getattr(prefs, 'phone_number', None),
            }
        except Exception as e:
            logger.error(f"Error in _get_prefs: {e}", exc_info=True)
            return None
    
    def _format_email_body(self, alert: Dict[str, Any]) -> str:
        """Format alert as email body"""
        severity_emoji = {
            'info': 'â„¹ï¸',
            'warning': 'âš ï¸',
            'critical': 'ðŸš¨',
        }
        emoji = severity_emoji.get(alert.get('severity', 'info'), 'â„¹ï¸')
        
        body = f"""
{emoji} AETHER-SCORE Alert: {alert.get('alert_type', 'Alert')}

{alert.get('message', '')}

"""
        
        if alert.get('suggested_actions'):
            body += "Suggested Actions:\n"
            for i, action in enumerate(alert['suggested_actions'], 1):
                body += f"{i}. {action}\n"
        
        body += "\n---\n"
        body += "This is an automated alert from AETHER-SCORE."
        
        return body



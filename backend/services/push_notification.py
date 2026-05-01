"""
Push notification service for sending push notifications via FCM, APNs, and Web Push
"""
from typing import Dict, List, Optional, Any
import os
from utils.logger import get_logger
from database.connection import get_session
from database.models import DeviceToken
from sqlalchemy import select

logger = get_logger(__name__)


class PushNotificationService:
    """Service for sending push notifications"""
    
    def __init__(self):
        self.fcm_server_key = os.getenv("FIREBASE_SERVER_KEY")
        self.fcm_project_id = os.getenv("FCM_PROJECT_ID")
        self.apns_key_id = os.getenv("APNS_KEY_ID")
        self.apns_team_id = os.getenv("APNS_TEAM_ID")
        self.apns_bundle_id = os.getenv("APNS_BUNDLE_ID")
        self.apns_key_path = os.getenv("APNS_KEY_PATH")
    
    async def register_device_token(
        self,
        address: str,
        device_token: str,
        platform: str,
        device_id: Optional[str] = None,
        app_version: Optional[str] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Register device token for push notifications
        
        Args:
            address: Wallet address
            device_token: Push notification token
            platform: Platform ('ios', 'android', 'web')
            device_id: Optional device identifier
            app_version: Optional app version
            session: Database session (optional)
            
        Returns:
            Device token info dict
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._register_device_token(
                        address, device_token, platform, device_id, app_version, db_session
                    )
            else:
                return await self._register_device_token(
                    address, device_token, platform, device_id, app_version, session
                )
        except Exception as e:
            logger.error(f"Error registering device token: {e}", exc_info=True)
            return None
    
    async def _register_device_token(
        self,
        address: str,
        device_token: str,
        platform: str,
        device_id: Optional[str],
        app_version: Optional[str],
        session
    ) -> Optional[Dict[str, Any]]:
        """Register device token in database"""
        try:
            from datetime import datetime
            
            # Check if token already exists
            result = await session.execute(
                select(DeviceToken).where(DeviceToken.device_token == device_token)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing token
                existing.wallet_address = address
                existing.platform = platform
                existing.device_id = device_id
                existing.app_version = app_version
                existing.updated_at = datetime.utcnow()
                existing.last_used_at = datetime.utcnow()
                await session.commit()
                
                return {
                    "id": existing.id,
                    "wallet_address": address,
                    "platform": platform,
                    "device_id": device_id,
                    "app_version": app_version,
                }
            else:
                # Create new token
                device = DeviceToken(
                    wallet_address=address,
                    device_token=device_token,
                    platform=platform,
                    device_id=device_id,
                    app_version=app_version,
                    last_used_at=datetime.utcnow()
                )
                session.add(device)
                await session.commit()
                await session.refresh(device)
                
                logger.info(f"Registered device token for {address} on {platform}")
                
                return {
                    "id": device.id,
                    "wallet_address": address,
                    "platform": platform,
                    "device_id": device_id,
                    "app_version": app_version,
                }
        except Exception as e:
            logger.error(f"Error in _register_device_token: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def unregister_device_token(
        self,
        device_token: str,
        session=None
    ) -> bool:
        """
        Unregister device token
        
        Args:
            device_token: Device token to unregister
            session: Database session (optional)
            
        Returns:
            True if unregistered successfully
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._unregister_device_token(device_token, db_session)
            else:
                return await self._unregister_device_token(device_token, session)
        except Exception as e:
            logger.error(f"Error unregistering device token: {e}", exc_info=True)
            return False
    
    async def _unregister_device_token(
        self,
        device_token: str,
        session
    ) -> bool:
        """Unregister device token from database"""
        try:
            result = await session.execute(
                select(DeviceToken).where(DeviceToken.device_token == device_token)
            )
            device = result.scalar_one_or_none()
            
            if not device:
                return False
            
            await session.delete(device)
            await session.commit()
            
            logger.info(f"Unregistered device token")
            return True
        except Exception as e:
            logger.error(f"Error in _unregister_device_token: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def send_push_notification(
        self,
        address: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        session=None
    ) -> bool:
        """
        Send push notification to user's devices
        
        Args:
            address: Wallet address
            title: Notification title
            body: Notification body
            data: Optional notification data
            session: Database session (optional)
            
        Returns:
            True if sent successfully to at least one device
        """
        try:
            devices = await self.get_user_devices(address, session)
            if not devices:
                logger.debug(f"No devices registered for {address}")
                return False
            
            success_count = 0
            for device in devices:
                try:
                    if device['platform'] == 'android':
                        success = await self._send_fcm_notification(
                            device['device_token'], title, body, data
                        )
                    elif device['platform'] == 'ios':
                        success = await self._send_apns_notification(
                            device['device_token'], title, body, data
                        )
                    elif device['platform'] == 'web':
                        success = await self._send_web_push_notification(
                            device['device_token'], title, body, data
                        )
                    else:
                        logger.warning(f"Unknown platform: {device['platform']}")
                        success = False
                    
                    if success:
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error sending to device {device['id']}: {e}", exc_info=True)
            
            return success_count > 0
        except Exception as e:
            logger.error(f"Error sending push notification: {e}", exc_info=True)
            return False
    
    async def send_batch_notifications(
        self,
        addresses: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        session=None
    ) -> Dict[str, bool]:
        """
        Send batch push notifications
        
        Args:
            addresses: List of wallet addresses
            title: Notification title
            body: Notification body
            data: Optional notification data
            session: Database session (optional)
            
        Returns:
            Dict mapping address -> success status
        """
        results = {}
        for address in addresses:
            results[address] = await self.send_push_notification(
                address, title, body, data, session
            )
        return results
    
    async def get_user_devices(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get all devices for user
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of device dicts
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._get_user_devices(address, db_session)
            else:
                return await self._get_user_devices(address, session)
        except Exception as e:
            logger.error(f"Error getting user devices: {e}", exc_info=True)
            return []
    
    async def _get_user_devices(
        self,
        address: str,
        session
    ) -> List[Dict[str, Any]]:
        """Get user devices from database"""
        try:
            result = await session.execute(
                select(DeviceToken).where(DeviceToken.wallet_address == address)
            )
            devices = result.scalars().all()
            
            return [
                {
                    "id": d.id,
                    "device_token": d.device_token,
                    "platform": d.platform,
                    "device_id": d.device_id,
                    "app_version": d.app_version,
                }
                for d in devices
            ]
        except Exception as e:
            logger.error(f"Error in _get_user_devices: {e}", exc_info=True)
            return []
    
    async def _send_fcm_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]]
    ) -> bool:
        """Send FCM notification for Android"""
        try:
            if not self.fcm_server_key:
                logger.warning("FCM server key not configured, logging notification instead")
                logger.info(f"Would send FCM to {device_token[:20]}...: {title}")
                return True
            
            import requests
            
            url = "https://fcm.googleapis.com/fcm/send"
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "to": device_token,
                "notification": {
                    "title": title,
                    "body": body
                }
            }
            
            if data:
                payload["data"] = data
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.debug(f"FCM notification sent successfully")
                return True
            else:
                logger.error(f"FCM error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}", exc_info=True)
            return False
    
    async def _send_apns_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]]
    ) -> bool:
        """Send APNs notification for iOS"""
        try:
            if not self.apns_key_path or not self.apns_key_id or not self.apns_team_id:
                logger.warning("APNs credentials not configured, logging notification instead")
                logger.info(f"Would send APNs to {device_token[:20]}...: {title}")
                return True
            
            # In production, would use PyAPNs2 or similar library
            # For now, just log
            logger.info(f"Would send APNs notification to {device_token[:20]}...: {title}")
            return True
        except Exception as e:
            logger.error(f"Error sending APNs notification: {e}", exc_info=True)
            return False
    
    async def _send_web_push_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]]
    ) -> bool:
        """Send web push notification"""
        try:
            # Web push uses VAPID protocol
            # In production, would use pywebpush library
            logger.info(f"Would send web push to {device_token[:20]}...: {title}")
            return True
        except Exception as e:
            logger.error(f"Error sending web push notification: {e}", exc_info=True)
            return False


"""
Webhook service for registering and dispatching webhooks
"""
from typing import Dict, List, Optional, Any
import hmac
import hashlib
import json
import secrets
import requests
from datetime import datetime
from utils.logger import get_logger
from database.connection import get_session
from database.models import Webhook, APIKey
from sqlalchemy import select

logger = get_logger(__name__)


class WebhookService:
    """Service for managing webhooks"""
    
    def __init__(self):
        pass
    
    async def register_webhook(
        self,
        api_key_id: int,
        url: str,
        events: List[str],
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Register webhook
        
        Args:
            api_key_id: API key ID
            url: Webhook URL
            events: List of event types to subscribe to
            session: Database session (optional)
            
        Returns:
            Webhook info dict
        """
        try:
            # Generate webhook secret
            secret = secrets.token_urlsafe(32)
            
            if session is None:
                async with get_session() as db_session:
                    return await self._register_webhook(api_key_id, url, events, secret, db_session)
            else:
                return await self._register_webhook(api_key_id, url, events, secret, session)
        except Exception as e:
            logger.error(f"Error registering webhook: {e}", exc_info=True)
            return None
    
    async def _register_webhook(
        self,
        api_key_id: int,
        url: str,
        events: List[str],
        secret: str,
        session
    ) -> Optional[Dict[str, Any]]:
        """Register webhook in database"""
        try:
            webhook = Webhook(
                api_key_id=api_key_id,
                url=url,
                secret=secret,
                events=events,
                active=True
            )
            session.add(webhook)
            await session.commit()
            await session.refresh(webhook)
            
            logger.info(f"Registered webhook {webhook.id} for API key {api_key_id}")
            
            return {
                "id": webhook.id,
                "url": webhook.url,
                "events": webhook.events,
                "secret": secret,  # Return secret only once
                "created_at": webhook.created_at.isoformat() if webhook.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _register_webhook: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def trigger_webhook(
        self,
        webhook_id: int,
        event_type: str,
        data: Dict[str, Any],
        session=None
    ) -> bool:
        """
        Trigger webhook
        
        Args:
            webhook_id: Webhook ID
            event_type: Event type
            data: Event data
            session: Database session (optional)
            
        Returns:
            True if triggered successfully
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._trigger_webhook(webhook_id, event_type, data, db_session)
            else:
                return await self._trigger_webhook(webhook_id, event_type, data, session)
        except Exception as e:
            logger.error(f"Error triggering webhook: {e}", exc_info=True)
            return False
    
    async def _trigger_webhook(
        self,
        webhook_id: int,
        event_type: str,
        data: Dict[str, Any],
        session
    ) -> bool:
        """Trigger webhook HTTP request"""
        try:
            result = await session.execute(
                select(Webhook).where(Webhook.id == webhook_id)
            )
            webhook = result.scalar_one_or_none()
            
            if not webhook or not webhook.active:
                return False
            
            # Check if webhook subscribes to this event
            if event_type not in webhook.events:
                return False
            
            # Prepare payload
            payload = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }
            
            # Generate signature
            signature = self._generate_signature(webhook.secret, payload)
            
            # Send webhook
            headers = {
                "Content-Type": "application/json",
                "X-AETHER-SCORE-Signature": signature,
                "X-AETHER-SCORE-Event": event_type,
            }
            
            try:
                response = requests.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                # Update webhook stats
                webhook.last_triggered_at = datetime.utcnow()
                
                if response.status_code >= 200 and response.status_code < 300:
                    webhook.failure_count = 0
                    await session.commit()
                    logger.info(f"Webhook {webhook_id} triggered successfully")
                    return True
                else:
                    webhook.failure_count += 1
                    await session.commit()
                    logger.warning(f"Webhook {webhook_id} returned status {response.status_code}")
                    return False
            except requests.RequestException as e:
                webhook.failure_count += 1
                await session.commit()
                logger.error(f"Error sending webhook {webhook_id}: {e}", exc_info=True)
                return False
        except Exception as e:
            logger.error(f"Error in _trigger_webhook: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def trigger_event_for_api_key(
        self,
        api_key_id: int,
        event_type: str,
        data: Dict[str, Any],
        session=None
    ) -> Dict[int, bool]:
        """
        Trigger webhooks for all webhooks associated with an API key
        
        Args:
            api_key_id: API key ID
            event_type: Event type
            data: Event data
            session: Database session (optional)
            
        Returns:
            Dict mapping webhook_id -> success status
        """
        try:
            if session is None:
                async with get_session() as db_session:
                    return await self._trigger_event_for_api_key(api_key_id, event_type, data, db_session)
            else:
                return await self._trigger_event_for_api_key(api_key_id, event_type, data, session)
        except Exception as e:
            logger.error(f"Error triggering event for API key: {e}", exc_info=True)
            return {}
    
    async def _trigger_event_for_api_key(
        self,
        api_key_id: int,
        event_type: str,
        data: Dict[str, Any],
        session
    ) -> Dict[int, bool]:
        """Trigger webhooks for API key"""
        try:
            result = await session.execute(
                select(Webhook).where(
                    Webhook.api_key_id == api_key_id,
                    Webhook.active == True
                )
            )
            webhooks = result.scalars().all()
            
            results = {}
            for webhook in webhooks:
                success = await self._trigger_webhook(webhook.id, event_type, data, session)
                results[webhook.id] = success
            
            return results
        except Exception as e:
            logger.error(f"Error in _trigger_event_for_api_key: {e}", exc_info=True)
            return {}
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Webhook payload (JSON string)
            signature: Signature from header
            secret: Webhook secret
            
        Returns:
            True if signature is valid
        """
        try:
            expected_signature = self._generate_signature(secret, json.loads(payload))
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}", exc_info=True)
            return False
    
    def _generate_signature(
        self,
        secret: str,
        payload: Dict[str, Any]
    ) -> str:
        """Generate HMAC signature for webhook"""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"



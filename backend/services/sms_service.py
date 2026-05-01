"""
SMS service for sending SMS notifications via Twilio or AWS SNS
"""
from typing import Dict, Optional, Any
import os
from utils.logger import get_logger

logger = get_logger(__name__)


class SMSService:
    """Service for sending SMS"""
    
    def __init__(self):
        self.provider = os.getenv("SMS_PROVIDER", "twilio").lower()
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.aws_sns_region = os.getenv("AWS_SNS_REGION")
    
    async def send_sms(
        self,
        to: str,
        message: str
    ) -> bool:
        """
        Send SMS
        
        Args:
            to: Recipient phone number (E.164 format)
            message: SMS message (max 1600 chars)
            
        Returns:
            True if sent successfully
        """
        try:
            # Truncate message if too long
            if len(message) > 1600:
                message = message[:1597] + "..."
            
            if self.provider == "twilio":
                return await self._send_via_twilio(to, message)
            elif self.provider == "sns":
                return await self._send_via_sns(to, message)
            else:
                logger.warning(f"Unknown SMS provider: {self.provider}, logging SMS instead")
                logger.info(f"Would send SMS to {to}: {message[:50]}...")
                return True
        except Exception as e:
            logger.error(f"Error sending SMS: {e}", exc_info=True)
            return False
    
    async def _send_via_twilio(
        self,
        to: str,
        message: str
    ) -> bool:
        """Send SMS via Twilio"""
        try:
            if not self.twilio_account_sid or not self.twilio_auth_token:
                logger.warning("Twilio credentials not configured, logging SMS instead")
                logger.info(f"Would send SMS to {to}: {message[:50]}...")
                return True
            
            from twilio.rest import Client
            
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            from_number = self.twilio_phone_number or "+1234567890"  # Default if not set
            
            response = client.messages.create(
                body=message,
                from_=from_number,
                to=to
            )
            
            logger.info(f"SMS sent to {to} via Twilio: {response.sid}")
            return True
        except ImportError:
            logger.warning("Twilio library not installed, logging SMS instead")
            logger.info(f"Would send SMS to {to}: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error sending via Twilio: {e}", exc_info=True)
            return False
    
    async def _send_via_sns(
        self,
        to: str,
        message: str
    ) -> bool:
        """Send SMS via AWS SNS"""
        try:
            if not self.aws_sns_region:
                logger.warning("AWS SNS region not configured, logging SMS instead")
                logger.info(f"Would send SMS to {to}: {message[:50]}...")
                return True
            
            import boto3
            
            sns_client = boto3.client('sns', region_name=self.aws_sns_region)
            
            response = sns_client.publish(
                PhoneNumber=to,
                Message=message
            )
            
            logger.info(f"SMS sent to {to} via AWS SNS: {response['MessageId']}")
            return True
        except ImportError:
            logger.warning("boto3 library not installed, logging SMS instead")
            logger.info(f"Would send SMS to {to}: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error sending via AWS SNS: {e}", exc_info=True)
            return False
    
    async def send_score_update_sms(
        self,
        address: str,
        old_score: int,
        new_score: int,
        phone: str
    ) -> bool:
        """Send score update SMS"""
        try:
            from services.sms_templates import get_score_update_sms
            
            message = await get_score_update_sms(address, old_score, new_score)
            return await self.send_sms(phone, message)
        except Exception as e:
            logger.error(f"Error sending score update SMS: {e}", exc_info=True)
            return False
    
    async def send_payment_reminder_sms(
        self,
        address: str,
        loan_info: Dict[str, Any],
        phone: str
    ) -> bool:
        """Send payment reminder SMS"""
        try:
            from services.sms_templates import get_payment_reminder_sms
            
            message = await get_payment_reminder_sms(address, loan_info)
            return await self.send_sms(phone, message)
        except Exception as e:
            logger.error(f"Error sending payment reminder SMS: {e}", exc_info=True)
            return False
    
    async def send_market_opportunity_sms(
        self,
        address: str,
        opportunity: Dict[str, Any],
        phone: str
    ) -> bool:
        """Send market opportunity SMS"""
        try:
            from services.sms_templates import get_market_opportunity_sms
            
            message = await get_market_opportunity_sms(address, opportunity)
            return await self.send_sms(phone, message)
        except Exception as e:
            logger.error(f"Error sending market opportunity SMS: {e}", exc_info=True)
            return False


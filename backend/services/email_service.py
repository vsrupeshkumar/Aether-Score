"""
Email service for sending email notifications via SendGrid, AWS SES, or SMTP
"""
from typing import Dict, Optional, Any
import os
from utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "sendgrid").lower()
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.aws_ses_region = os.getenv("AWS_SES_REGION")
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@AETHER-SCORE.io")
        self.from_name = os.getenv("FROM_NAME", "AETHER-SCORE")
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send email
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            
        Returns:
            True if sent successfully
        """
        try:
            if self.provider == "sendgrid":
                return await self._send_via_sendgrid(to, subject, body, html_body)
            elif self.provider == "ses":
                return await self._send_via_ses(to, subject, body, html_body)
            elif self.provider == "smtp":
                return await self._send_via_smtp(to, subject, body, html_body)
            else:
                logger.warning(f"Unknown email provider: {self.provider}, logging email instead")
                logger.info(f"Would send email to {to}: {subject}")
                return True
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return False
    
    async def _send_via_sendgrid(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str]
    ) -> bool:
        """Send email via SendGrid"""
        try:
            if not self.sendgrid_api_key:
                logger.warning("SendGrid API key not configured, logging email instead")
                logger.info(f"Would send email to {to}: {subject}")
                return True
            
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            from_email = Email(self.from_email, self.from_name)
            to_email = Email(to)
            
            if html_body:
                content = Content("text/html", html_body)
            else:
                content = Content("text/plain", body)
            
            message = Mail(from_email, to_email, subject, content)
            
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent to {to} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False
        except ImportError:
            logger.warning("SendGrid library not installed, logging email instead")
            logger.info(f"Would send email to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Error sending via SendGrid: {e}", exc_info=True)
            return False
    
    async def _send_via_ses(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str]
    ) -> bool:
        """Send email via AWS SES"""
        try:
            if not self.aws_ses_region:
                logger.warning("AWS SES region not configured, logging email instead")
                logger.info(f"Would send email to {to}: {subject}")
                return True
            
            import boto3
            
            ses_client = boto3.client('ses', region_name=self.aws_ses_region)
            
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body, 'Charset': 'UTF-8'},
                }
            }
            
            if html_body:
                message['Body']['Html'] = {'Data': html_body, 'Charset': 'UTF-8'}
            
            response = ses_client.send_email(
                Source=f"{self.from_name} <{self.from_email}>",
                Destination={'ToAddresses': [to]},
                Message=message
            )
            
            logger.info(f"Email sent to {to} via AWS SES: {response['MessageId']}")
            return True
        except ImportError:
            logger.warning("boto3 library not installed, logging email instead")
            logger.info(f"Would send email to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Error sending via AWS SES: {e}", exc_info=True)
            return False
    
    async def _send_via_smtp(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str]
    ) -> bool:
        """Send email via SMTP"""
        try:
            if not self.smtp_host:
                logger.warning("SMTP not configured, logging email instead")
                logger.info(f"Would send email to {to}: {subject}")
                return True
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to
            
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)
            
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to} via SMTP")
            return True
        except Exception as e:
            logger.error(f"Error sending via SMTP: {e}", exc_info=True)
            return False
    
    async def send_score_update_email(
        self,
        address: str,
        old_score: int,
        new_score: int,
        email: str
    ) -> bool:
        """Send score update email"""
        try:
            from services.email_templates import get_score_update_template
            
            subject = "Your AETHER-SCORE Score Has Been Updated"
            html_body, text_body = await get_score_update_template(address, old_score, new_score)
            
            return await self.send_email(email, subject, text_body, html_body)
        except Exception as e:
            logger.error(f"Error sending score update email: {e}", exc_info=True)
            return False
    
    async def send_payment_reminder_email(
        self,
        address: str,
        loan_info: Dict[str, Any],
        email: str
    ) -> bool:
        """Send payment reminder email"""
        try:
            from services.email_templates import get_payment_reminder_template
            
            subject = f"Payment Reminder: Loan #{loan_info.get('loan_id', 'N/A')}"
            html_body, text_body = await get_payment_reminder_template(address, loan_info)
            
            return await self.send_email(email, subject, text_body, html_body)
        except Exception as e:
            logger.error(f"Error sending payment reminder email: {e}", exc_info=True)
            return False
    
    async def send_market_opportunity_email(
        self,
        address: str,
        opportunity: Dict[str, Any],
        email: str
    ) -> bool:
        """Send market opportunity email"""
        try:
            from services.email_templates import get_market_opportunity_template
            
            subject = f"Market Opportunity: {opportunity.get('type', 'New Opportunity')}"
            html_body, text_body = await get_market_opportunity_template(address, opportunity)
            
            return await self.send_email(email, subject, text_body, html_body)
        except Exception as e:
            logger.error(f"Error sending market opportunity email: {e}", exc_info=True)
            return False
    
    async def send_welcome_email(
        self,
        address: str,
        email: str
    ) -> bool:
        """Send welcome email"""
        try:
            from services.email_templates import get_welcome_template
            
            subject = "Welcome to AETHER-SCORE!"
            html_body, text_body = await get_welcome_template(address)
            
            return await self.send_email(email, subject, text_body, html_body)
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}", exc_info=True)
            return False



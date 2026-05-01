"""
Email template service for generating email content
"""
from typing import Tuple, Dict, Any
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


async def get_score_update_template(
    address: str,
    old_score: int,
    new_score: int
) -> Tuple[str, str]:
    """
    Get score update email template
    
    Returns:
        Tuple of (html_body, text_body)
    """
    score_change = new_score - old_score
    change_text = f"+{score_change}" if score_change > 0 else str(score_change)
    change_emoji = "ðŸ“ˆ" if score_change > 0 else "ðŸ“‰" if score_change < 0 else "âž¡ï¸"
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .score-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
        .score {{ font-size: 48px; font-weight: bold; color: #667eea; }}
        .change {{ font-size: 24px; color: {'#10b981' if score_change > 0 else '#ef4444' if score_change < 0 else '#6b7280'}; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AETHER-SCORE Score Update</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>Your AETHER-SCORE credit score has been updated!</p>
            
            <div class="score-box">
                <div class="score">{new_score}</div>
                <div class="change">{change_emoji} {change_text} points</div>
                <p style="margin-top: 10px; color: #6b7280;">Previous score: {old_score}</p>
            </div>
            
            <p>Keep up the great work to maintain and improve your credit score!</p>
            
            <p>Best regards,<br>The AETHER-SCORE Team</p>
        </div>
        <div class="footer">
            <p>This is an automated email from AETHER-SCORE. Wallet: {address[:10]}...{address[-8:]}</p>
        </div>
    </div>
</body>
</html>
"""
    
    text_body = f"""
AETHER-SCORE Score Update

Hello,

Your AETHER-SCORE credit score has been updated!

New Score: {new_score}
Change: {change_text} points
Previous Score: {old_score}

Keep up the great work to maintain and improve your credit score!

Best regards,
The AETHER-SCORE Team

---
This is an automated email from AETHER-SCORE. Wallet: {address[:10]}...{address[-8:]}
"""
    
    return html_body, text_body


async def get_payment_reminder_template(
    address: str,
    loan_info: Dict[str, Any]
) -> Tuple[str, str]:
    """Get payment reminder email template"""
    loan_id = loan_info.get('loan_id', 'N/A')
    amount = loan_info.get('amount_due', 0)
    due_date = loan_info.get('due_date', 'N/A')
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f59e0b; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .alert-box {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>âš ï¸ Payment Reminder</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>This is a reminder that you have an upcoming loan payment.</p>
            
            <div class="alert-box">
                <h3>Loan #{loan_id}</h3>
                <p><strong>Amount Due:</strong> {amount}</p>
                <p><strong>Due Date:</strong> {due_date}</p>
            </div>
            
            <p>Please ensure you have sufficient funds to make this payment on time.</p>
            
            <p>Best regards,<br>The AETHER-SCORE Team</p>
        </div>
        <div class="footer">
            <p>This is an automated email from AETHER-SCORE. Wallet: {address[:10]}...{address[-8:]}</p>
        </div>
    </div>
</body>
</html>
"""
    
    text_body = f"""
Payment Reminder

Hello,

This is a reminder that you have an upcoming loan payment.

Loan #{loan_id}
Amount Due: {amount}
Due Date: {due_date}

Please ensure you have sufficient funds to make this payment on time.

Best regards,
The AETHER-SCORE Team

---
This is an automated email from AETHER-SCORE. Wallet: {address[:10]}...{address[-8:]}
"""
    
    return html_body, text_body


async def get_market_opportunity_template(
    address: str,
    opportunity: Dict[str, Any]
) -> Tuple[str, str]:
    """Get market opportunity email template"""
    opp_type = opportunity.get('type', 'New Opportunity')
    description = opportunity.get('description', '')
    action_url = opportunity.get('action_url', '#')
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #10b981; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .opportunity-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981; }}
        .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ðŸ’° Market Opportunity</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>We've found a market opportunity that might interest you!</p>
            
            <div class="opportunity-box">
                <h3>{opp_type}</h3>
                <p>{description}</p>
                <a href="{action_url}" class="button">View Opportunity</a>
            </div>
            
            <p>Best regards,<br>The AETHER-SCORE Team</p>
        </div>
        <div class="footer">
            <p>This is an automated email from AETHER-SCORE. Wallet: {address[:10]}...{address[-8:]}</p>
        </div>
    </div>
</body>
</html>
"""
    
    text_body = f"""
Market Opportunity

Hello,

We've found a market opportunity that might interest you!

{opp_type}
{description}

View Opportunity: {action_url}

Best regards,
The AETHER-SCORE Team

---
This is an automated email from AETHER-SCORE. Wallet: {address[:10]}...{address[-8:]}
"""
    
    return html_body, text_body


async def get_welcome_template(
    address: str
) -> Tuple[str, str]:
    """Get welcome email template"""
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to AETHER-SCORE!</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>Welcome to AETHER-SCORE - your AI-powered credit passport on the QIE blockchain!</p>
            
            <p>With AETHER-SCORE, you can:</p>
            <ul>
                <li>Get your on-chain credit score</li>
                <li>Access DeFi lending opportunities</li>
                <li>Build your credit reputation</li>
                <li>Stake tokens to boost your score</li>
            </ul>
            
            <p>Get started by connecting your wallet and generating your first credit score!</p>
            
            <p>Best regards,<br>The AETHER-SCORE Team</p>
        </div>
        <div class="footer">
            <p>This is an automated email from AETHER-SCORE. Wallet: {address[:10]}...{address[-8:]}</p>
        </div>
    </div>
</body>
</html>
"""
    
    text_body = f"""
Welcome to AETHER-SCORE!

Hello,

Welcome to AETHER-SCORE - your AI-powered credit passport on the QIE blockchain!

With AETHER-SCORE, you can:
- Get your on-chain credit score
- Access DeFi lending opportunities
- Build your credit reputation
- Stake tokens to boost your score

Get started by connecting your wallet and generating your first credit score!

Best regards,
The AETHER-SCORE Team

---
This is an automated email from AETHER-SCORE. Wallet: {address[:10]}...{address[-8:]}
"""
    
    return html_body, text_body



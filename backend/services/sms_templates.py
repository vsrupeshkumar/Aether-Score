"""
SMS template service for generating SMS messages
"""
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


async def get_score_update_sms(
    address: str,
    old_score: int,
    new_score: int
) -> str:
    """Get score update SMS message"""
    score_change = new_score - old_score
    change_text = f"+{score_change}" if score_change > 0 else str(score_change)
    emoji = "ðŸ“ˆ" if score_change > 0 else "ðŸ“‰" if score_change < 0 else "âž¡ï¸"
    
    return f"AETHER-SCORE: Your score updated to {new_score} ({emoji} {change_text}). Previous: {old_score}. Wallet: {address[:6]}...{address[-4:]}"


async def get_payment_reminder_sms(
    address: str,
    loan_info: Dict[str, Any]
) -> str:
    """Get payment reminder SMS message"""
    loan_id = loan_info.get('loan_id', 'N/A')
    amount = loan_info.get('amount_due', 0)
    due_date = loan_info.get('due_date', 'N/A')
    
    return f"AETHER-SCORE: Payment reminder for Loan #{loan_id}. Amount: {amount}, Due: {due_date}. Wallet: {address[:6]}...{address[-4:]}"


async def get_market_opportunity_sms(
    address: str,
    opportunity: Dict[str, Any]
) -> str:
    """Get market opportunity SMS message"""
    opp_type = opportunity.get('type', 'New Opportunity')
    description = opportunity.get('description', '')
    
    # Truncate description if too long
    if len(description) > 100:
        description = description[:97] + "..."
    
    return f"AETHER-SCORE: Market opportunity - {opp_type}. {description}. Wallet: {address[:6]}...{address[-4:]}"



"""
Risk monitor service for detecting score drops and loan risks
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from utils.logger import get_logger
from services.scoring import ScoringService
from services.loan_service import LoanService
from database.repositories import ScoreHistoryRepository

logger = get_logger(__name__)


class RiskMonitor:
    """Service for monitoring risk events and generating alerts"""
    
    # Score drop thresholds
    SCORE_DROP_ABSOLUTE = 50  # Absolute drop threshold
    SCORE_DROP_PERCENTAGE = 0.10  # 10% drop threshold
    
    # Loan risk thresholds
    HIGH_LTV_THRESHOLD = 0.80  # 80% LTV
    MATURITY_WARNING_DAYS = 7  # Warn 7 days before maturity
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.loan_service = LoanService()
    
    async def monitor_score_changes(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Monitor score for significant drops
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of detected risk events
        """
        try:
            from database.connection import get_session
            from database.repositories import ScoreRepository, ScoreHistoryRepository
            
            if session is None:
                async with get_session() as db_session:
                    return await self._monitor_score_changes(address, db_session)
            else:
                return await self._monitor_score_changes(address, session)
        except Exception as e:
            logger.error(f"Error monitoring score changes: {e}", exc_info=True)
            return []
    
    async def _monitor_score_changes(
        self,
        address: str,
        session
    ) -> List[Dict[str, Any]]:
        """Monitor score changes from database"""
        from database.repositories import ScoreRepository, ScoreHistoryRepository
        from datetime import datetime, timedelta
        
        try:
            # Get current score
            current_score_obj = await ScoreRepository.get_score(session, address)
            if not current_score_obj:
                return []
            
            current_score = current_score_obj.score
            
            # Get score history (last 30 days)
            start_date = datetime.utcnow() - timedelta(days=30)
            history = await ScoreHistoryRepository.get_history(
                session, address, limit=100, start_date=start_date
            )
            
            if not history:
                return []
            
            # Find previous score (most recent before now)
            previous_score = history[0].score if history else current_score
            
            # Check for significant drop
            events = []
            score_drop = current_score - previous_score
            
            # Check absolute drop
            if score_drop <= -self.SCORE_DROP_ABSOLUTE:
                events.append({
                    "type": "score_drop_absolute",
                    "severity": "warning" if abs(score_drop) < 100 else "critical",
                    "current_score": current_score,
                    "previous_score": previous_score,
                    "drop_amount": abs(score_drop),
                    "message": f"Credit score dropped by {abs(score_drop)} points",
                })
            
            # Check percentage drop
            if previous_score > 0:
                drop_percentage = abs(score_drop) / previous_score
                if drop_percentage >= self.SCORE_DROP_PERCENTAGE:
                    events.append({
                        "type": "score_drop_percentage",
                        "severity": "warning" if drop_percentage < 0.20 else "critical",
                        "current_score": current_score,
                        "previous_score": previous_score,
                        "drop_percentage": drop_percentage,
                        "message": f"Credit score dropped by {drop_percentage:.1%}",
                    })
            
            return events
        except Exception as e:
            logger.error(f"Error in _monitor_score_changes: {e}", exc_info=True)
            return []
    
    async def check_loan_risk(
        self,
        address: str,
        loan_id: Optional[int] = None,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Check individual loan risk
        
        Args:
            address: Wallet address
            loan_id: Specific loan ID (optional, checks all if None)
            session: Database session (optional)
            
        Returns:
            List of loan risk events
        """
        try:
            # Get user's loans
            loans = await self.loan_service.get_user_loans(address)
            
            events = []
            
            for loan in loans:
                if loan_id and loan.get('id') != loan_id:
                    continue
                
                loan_events = await self._check_single_loan_risk(loan)
                events.extend(loan_events)
            
            return events
        except Exception as e:
            logger.error(f"Error checking loan risk: {e}", exc_info=True)
            return []
    
    async def _check_single_loan_risk(
        self,
        loan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check risk for a single loan"""
        events = []
        
        # Check LTV ratio
        ltv = loan.get('ltv_ratio')
        if ltv and ltv > self.HIGH_LTV_THRESHOLD:
            events.append({
                "type": "high_ltv",
                "severity": "warning" if ltv < 0.90 else "critical",
                "loan_id": loan.get('id'),
                "ltv_ratio": ltv,
                "message": f"Loan has high LTV ratio: {ltv:.1%}",
            })
        
        # Check maturity date
        maturity_date = loan.get('maturity_date')
        if maturity_date:
            try:
                if isinstance(maturity_date, str):
                    maturity = datetime.fromisoformat(maturity_date.replace('Z', '+00:00'))
                else:
                    maturity = maturity_date
                
                days_until_maturity = (maturity - datetime.utcnow()).days
                
                if 0 < days_until_maturity <= self.MATURITY_WARNING_DAYS:
                    events.append({
                        "type": "repayment_reminder",
                        "severity": "warning",
                        "loan_id": loan.get('id'),
                        "days_until_maturity": days_until_maturity,
                        "message": f"Loan repayment due in {days_until_maturity} days",
                    })
                elif days_until_maturity < 0:
                    events.append({
                        "type": "loan_overdue",
                        "severity": "critical",
                        "loan_id": loan.get('id'),
                        "days_overdue": abs(days_until_maturity),
                        "message": f"Loan is {abs(days_until_maturity)} days overdue",
                    })
            except Exception as e:
                logger.warning(f"Error parsing maturity date: {e}")
        
        # Check loan status
        status = loan.get('status')
        if status == 'defaulted':
            events.append({
                "type": "loan_defaulted",
                "severity": "critical",
                "loan_id": loan.get('id'),
                "message": "Loan has defaulted",
            })
        
        return events
    
    async def detect_risk_events(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Detect various risk events for a user
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of all detected risk events
        """
        try:
            events = []
            
            # Monitor score changes
            score_events = await self.monitor_score_changes(address, session)
            events.extend(score_events)
            
            # Check loan risks
            loan_events = await self.check_loan_risk(address, session=session)
            events.extend(loan_events)
            
            # Check market volatility (if available)
            market_events = await self._check_market_volatility(address)
            events.extend(market_events)
            
            return events
        except Exception as e:
            logger.error(f"Error detecting risk events: {e}", exc_info=True)
            return []
    
    async def generate_risk_alerts(
        self,
        address: str,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Generate alerts for detected risks
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            List of alert dicts
        """
        try:
            events = await self.detect_risk_events(address, session)
            
            alerts = []
            for event in events:
                alert = {
                    "alert_type": event.get("type"),
                    "severity": event.get("severity", "warning"),
                    "message": event.get("message", "Risk event detected"),
                    "suggested_actions": self._get_suggested_actions(event),
                    "metadata": {k: v for k, v in event.items() if k not in ['type', 'severity', 'message']},
                }
                alerts.append(alert)
            
            return alerts
        except Exception as e:
            logger.error(f"Error generating risk alerts: {e}", exc_info=True)
            return []
    
    def _get_suggested_actions(
        self,
        event: Dict[str, Any]
    ) -> List[str]:
        """Get suggested actions for a risk event"""
        event_type = event.get("type")
        
        actions_map = {
            "score_drop_absolute": [
                "Review recent transactions",
                "Consider repaying existing loans early",
                "Increase staking to boost score",
            ],
            "score_drop_percentage": [
                "Your credit score has decreased significantly",
                "Consider repaying loans early to improve score",
                "Review your on-chain activity",
            ],
            "high_ltv": [
                "Add more collateral to reduce LTV ratio",
                "Consider repaying part of the loan",
            ],
            "repayment_reminder": [
                "Ensure sufficient funds for repayment",
                "Set up automatic repayment if available",
            ],
            "loan_overdue": [
                "Repay loan immediately to avoid penalties",
                "Contact lender to discuss options",
            ],
            "loan_defaulted": [
                "Contact lender immediately",
                "Review loan terms and options",
            ],
        }
        
        return actions_map.get(event_type, ["Review your account status"])
    
    async def _check_market_volatility(
        self,
        address: str
    ) -> List[Dict[str, Any]]:
        """Check market volatility risks"""
        try:
            from services.oracle import QIEOracleService
            
            oracle = QIEOracleService()
            volatility = await oracle.get_volatility('ETH', days=7)
            
            events = []
            if volatility and volatility > 0.5:  # High volatility threshold
                events.append({
                    "type": "market_volatility",
                    "severity": "warning",
                    "volatility": volatility,
                    "message": f"High market volatility detected ({volatility:.1%})",
                })
            
            return events
        except Exception as e:
            logger.error(f"Error checking market volatility: {e}", exc_info=True)
            return []


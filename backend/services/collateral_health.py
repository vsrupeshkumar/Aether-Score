"""
Collateral health monitor service for tracking collateral health and generating alerts
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from services.collateral_manager import CollateralManager

logger = get_logger(__name__)


class CollateralHealthMonitor:
    """Service for monitoring collateral health"""
    
    # Health thresholds
    HEALTH_SAFE = 0.7
    HEALTH_WARNING = 0.5
    HEALTH_CRITICAL = 0.5  # Below this is liquidation risk
    
    def __init__(self):
        self.collateral_manager = CollateralManager()
    
    async def monitor_health(
        self,
        loan_id: int,
        session=None
    ) -> Dict[str, Any]:
        """
        Monitor collateral health for a loan
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            Health status dict
        """
        try:
            health_ratio = await self.calculate_health_ratio(loan_id, session)
            ltv = await self.collateral_manager.calculate_ltv(loan_id, session)
            
            if health_ratio is None:
                return {
                    "loan_id": loan_id,
                    "status": "unknown",
                    "health_ratio": None,
                    "ltv": ltv,
                    "alerts": [],
                }
            
            status = self._get_health_status(health_ratio)
            alerts = await self.get_health_alerts(loan_id, session)
            
            return {
                "loan_id": loan_id,
                "status": status,
                "health_ratio": health_ratio,
                "ltv": ltv,
                "alerts": alerts,
                "liquidation_risk": health_ratio < self.HEALTH_CRITICAL,
            }
        except Exception as e:
            logger.error(f"Error monitoring health: {e}", exc_info=True)
            return {
                "loan_id": loan_id,
                "status": "error",
                "health_ratio": None,
                "ltv": None,
                "alerts": [],
            }
    
    async def calculate_health_ratio(
        self,
        loan_id: int,
        session=None
    ) -> Optional[float]:
        """
        Calculate collateral health ratio (0-1)
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            Health ratio (0-1) or None
        """
        try:
            from database.connection import get_session
            from database.models import Loan
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._calculate_health_ratio(loan_id, db_session)
            else:
                return await self._calculate_health_ratio(loan_id, session)
        except Exception as e:
            logger.error(f"Error calculating health ratio: {e}", exc_info=True)
            return None
    
    async def _calculate_health_ratio(
        self,
        loan_id: int,
        session
    ) -> Optional[float]:
        """Calculate health ratio from database"""
        from database.models import Loan
        from sqlalchemy import select
        
        try:
            # Get loan
            loan_result = await session.execute(
                select(Loan).where(Loan.id == loan_id)
            )
            loan = loan_result.scalar_one_or_none()
            
            if not loan:
                return None
            
            loan_amount = Decimal(str(loan.principal_amount))
            collateral_value = await self.collateral_manager.calculate_total_collateral_value(loan_id, session)
            
            if collateral_value == 0:
                return 0.0
            
            # Health ratio: collateral_value / loan_amount
            # Higher is better (more collateral relative to loan)
            health_ratio = float(collateral_value / loan_amount)
            
            # Normalize to 0-1 scale (assuming max LTV of 0.8 means health of 1.25)
            # Health of 1.0 = 100% collateral coverage
            # Health of 0.5 = 50% collateral coverage (critical)
            normalized_health = min(1.0, health_ratio)
            
            return normalized_health
        except Exception as e:
            logger.error(f"Error in _calculate_health_ratio: {e}", exc_info=True)
            return None
    
    async def check_liquidation_risk(
        self,
        loan_id: int,
        session=None
    ) -> bool:
        """
        Check if loan is at liquidation risk
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            True if at liquidation risk
        """
        try:
            health_ratio = await self.calculate_health_ratio(loan_id, session)
            
            if health_ratio is None:
                return False
            
            return health_ratio < self.HEALTH_CRITICAL
        except Exception as e:
            logger.error(f"Error checking liquidation risk: {e}", exc_info=True)
            return False
    
    async def get_health_alerts(
        self,
        loan_id: int,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get health alerts for a loan
        
        Args:
            loan_id: Loan ID
            session: Database session (optional)
            
        Returns:
            List of alert dicts
        """
        try:
            alerts = []
            
            health_ratio = await self.calculate_health_ratio(loan_id, session)
            
            if health_ratio is None:
                alerts.append({
                    "type": "unknown",
                    "severity": "info",
                    "message": "Unable to calculate health ratio",
                })
                return alerts
            
            # Check health thresholds
            if health_ratio < self.HEALTH_CRITICAL:
                alerts.append({
                    "type": "liquidation_risk",
                    "severity": "critical",
                    "message": f"Collateral health is critical ({health_ratio:.2%}). Liquidation risk imminent.",
                })
            elif health_ratio < self.HEALTH_WARNING:
                alerts.append({
                    "type": "low_collateral",
                    "severity": "warning",
                    "message": f"Collateral health is low ({health_ratio:.2%}). Consider adding more collateral.",
                })
            
            # Check LTV
            ltv = await self.collateral_manager.calculate_ltv(loan_id, session)
            if ltv and ltv > 0.8:
                alerts.append({
                    "type": "high_ltv",
                    "severity": "warning",
                    "message": f"Loan-to-value ratio is high ({ltv:.2%}). Consider reducing loan amount or adding collateral.",
                })
            
            # Check positions
            positions = await self.collateral_manager.get_collateral_positions(loan_id, session)
            if not positions:
                alerts.append({
                    "type": "no_collateral",
                    "severity": "warning",
                    "message": "No collateral positions found for this loan.",
                })
            
            return alerts
        except Exception as e:
            logger.error(f"Error getting health alerts: {e}", exc_info=True)
            return []
    
    def _get_health_status(self, health_ratio: float) -> str:
        """
        Get health status string
        
        Args:
            health_ratio: Health ratio (0-1)
            
        Returns:
            Status string
        """
        if health_ratio >= self.HEALTH_SAFE:
            return "safe"
        elif health_ratio >= self.HEALTH_WARNING:
            return "warning"
        else:
            return "critical"


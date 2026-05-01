"""
Activity monitor service for real-time activity tracking and score adjustments
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from utils.logger import get_logger

logger = get_logger(__name__)


class ActivityMonitor:
    """Service for monitoring recent activity and calculating real-time score adjustments"""
    
    # Time windows for activity monitoring
    RECENT_WINDOW_HOURS = 24
    ACTIVITY_SPIKE_THRESHOLD = 10  # Transactions per hour
    
    # Score adjustments
    POSITIVE_ACTIVITY_BOOST = 5  # Points for positive activity
    NEGATIVE_ACTIVITY_PENALTY = -10  # Points for negative activity (failed txs, etc.)
    MAX_REALTIME_ADJUSTMENT = 20  # Maximum adjustment in either direction
    
    async def monitor_recent_activity(
        self,
        address: str,
        hours: int = RECENT_WINDOW_HOURS,
        session=None
    ) -> Dict[str, Any]:
        """
        Monitor recent activity for an address
        
        Args:
            address: Wallet address
            hours: Hours to look back
            session: Database session (optional)
            
        Returns:
            Activity summary dict
        """
        try:
            from database.connection import get_session
            from database.models import Transaction
            from sqlalchemy import select, func, and_
            from datetime import datetime, timedelta
            
            if session is None:
                async with get_session() as db_session:
                    return await self._monitor_activity(address, hours, db_session)
            else:
                return await self._monitor_activity(address, hours, session)
        except Exception as e:
            logger.error(f"Error monitoring activity: {e}", exc_info=True)
            return {}
    
    async def _monitor_activity(self, address: str, hours: int, session) -> Dict[str, Any]:
        """Monitor activity from database"""
        from database.models import Transaction
        from sqlalchemy import select, func, and_
        from datetime import datetime, timedelta
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get recent transactions
            result = await session.execute(
                select(Transaction)
                .where(
                    and_(
                        Transaction.wallet_address == address,
                        Transaction.block_timestamp >= cutoff_time
                    )
                )
                .order_by(Transaction.block_timestamp.desc())
            )
            transactions = result.scalars().all()
            
            # Analyze activity
            total_txs = len(transactions)
            successful_txs = sum(1 for tx in transactions if tx.status == 'success')
            failed_txs = sum(1 for tx in transactions if tx.status == 'failed')
            
            # Calculate volume
            total_volume = sum(
                float(tx.value) / 1e18 if tx.value and tx.status == 'success' else 0
                for tx in transactions
            )
            
            # Group by hour
            hourly_counts = defaultdict(int)
            for tx in transactions:
                if tx.block_timestamp:
                    hour_key = tx.block_timestamp.replace(minute=0, second=0, microsecond=0)
                    hourly_counts[hour_key] += 1
            
            max_hourly_txs = max(hourly_counts.values()) if hourly_counts else 0
            
            return {
                "total_transactions": total_txs,
                "successful_transactions": successful_txs,
                "failed_transactions": failed_txs,
                "total_volume": total_volume,
                "max_hourly_transactions": max_hourly_txs,
                "success_rate": successful_txs / total_txs if total_txs > 0 else 0,
                "hours_monitored": hours,
            }
        except Exception as e:
            logger.error(f"Error in _monitor_activity: {e}", exc_info=True)
            return {}
    
    async def detect_activity_spike(
        self,
        address: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Detect unusual activity spike
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Spike info if detected, None otherwise
        """
        try:
            activity = await self.monitor_recent_activity(address, hours=1, session=session)
            
            if activity.get("total_transactions", 0) > self.ACTIVITY_SPIKE_THRESHOLD:
                return {
                    "is_spike": True,
                    "transaction_count": activity["total_transactions"],
                    "threshold": self.ACTIVITY_SPIKE_THRESHOLD,
                    "severity": "high" if activity["total_transactions"] > self.ACTIVITY_SPIKE_THRESHOLD * 2 else "medium",
                }
            
            return None
        except Exception as e:
            logger.error(f"Error detecting activity spike: {e}", exc_info=True)
            return None
    
    async def calculate_realtime_adjustment(
        self,
        address: str,
        session=None
    ) -> int:
        """
        Calculate real-time score adjustment based on recent activity
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Score adjustment (-MAX to +MAX)
        """
        try:
            activity = await self.monitor_recent_activity(address, session=session)
            
            if not activity:
                return 0
            
            adjustment = 0
            
            # Positive factors
            success_rate = activity.get("success_rate", 0)
            if success_rate > 0.9:  # High success rate
                adjustment += self.POSITIVE_ACTIVITY_BOOST
            
            total_volume = activity.get("total_volume", 0)
            if total_volume > 100:  # Significant volume
                adjustment += 5
            
            # Negative factors
            failed_txs = activity.get("failed_transactions", 0)
            if failed_txs > 5:  # Many failed transactions
                adjustment += self.NEGATIVE_ACTIVITY_PENALTY
            
            # Check for activity spike (could be bot or suspicious)
            spike = await self.detect_activity_spike(address, session)
            if spike and spike.get("severity") == "high":
                adjustment -= 5  # Penalty for suspicious activity
            
            # Cap adjustment
            adjustment = max(-self.MAX_REALTIME_ADJUSTMENT, min(self.MAX_REALTIME_ADJUSTMENT, adjustment))
            
            return adjustment
        except Exception as e:
            logger.error(f"Error calculating realtime adjustment: {e}", exc_info=True)
            return 0


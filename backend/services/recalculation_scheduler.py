"""
Recalculation Scheduler

Schedules periodic score recalculations.
"""

import os
import schedule
import time
from typing import Dict, Any
from services.score_recalculation import ScoreRecalculationService
from utils.logger import get_logger

logger = get_logger(__name__)


class RecalculationScheduler:
    """Scheduler for periodic score recalculations"""
    
    def __init__(self):
        self.recalculation_service = ScoreRecalculationService()
        self.schedule_interval = os.getenv("RECALCULATION_SCHEDULE", "daily")  # daily, weekly, hourly
    
    def setup_schedule(self):
        """Setup recurring schedule"""
        if self.schedule_interval == "hourly":
            schedule.every().hour.do(self._run_recalculation)
        elif self.schedule_interval == "daily":
            schedule.every().day.at("02:00").do(self._run_recalculation)  # 2 AM
        elif self.schedule_interval == "weekly":
            schedule.every().week.do(self._run_recalculation)
        else:
            schedule.every().day.at("02:00").do(self._run_recalculation)  # Default daily
        
        logger.info(f"Recalculation schedule set to: {self.schedule_interval}")
    
    def _run_recalculation(self):
        """Run recalculation (synchronous wrapper)"""
        import asyncio
        try:
            result = asyncio.run(self.recalculation_service.batch_recalculate())
            logger.info(f"Scheduled recalculation completed", extra=result)
        except Exception as e:
            logger.error(f"Error in scheduled recalculation: {e}", exc_info=True)
    
    def run(self):
        """Run scheduler loop"""
        self.setup_schedule()
        
        logger.info("Recalculation scheduler started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


"""
A/B Testing Framework

Experiment tracking, user allocation, metric collection, and statistical analysis.
"""

import os
import hashlib
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from database.models import ABExperiment, ABAllocation, ABMetric
from database.connection import get_db_session
from utils.logger import get_logger

logger = get_logger(__name__)


class ABTestingService:
    """Service for A/B testing"""
    
    def __init__(self):
        self.default_allocation_ratio = 0.5  # 50/50 split
    
    async def create_experiment(
        self,
        experiment_name: str,
        variant_a_name: str,
        variant_b_name: str,
        description: Optional[str] = None,
        allocation_ratio: float = 0.5
    ) -> Dict[str, Any]:
        """
        Create a new A/B experiment
        
        Returns:
            Experiment details
        """
        try:
            async with get_db_session() as session:
                # Check if experiment exists
                stmt = select(ABExperiment).where(
                    ABExperiment.experiment_name == experiment_name
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    return {
                        "status": "error",
                        "error": "Experiment already exists",
                    }
                
                # Create experiment
                experiment = ABExperiment(
                    experiment_name=experiment_name,
                    description=description,
                    variant_a_name=variant_a_name,
                    variant_b_name=variant_b_name,
                    allocation_ratio=allocation_ratio,
                    status="draft"
                )
                
                session.add(experiment)
                await session.commit()
                await session.refresh(experiment)
                
                logger.info(f"Created A/B experiment: {experiment_name}")
                
                return {
                    "status": "success",
                    "experiment_id": experiment.id,
                    "experiment_name": experiment_name,
                }
                
        except Exception as e:
            logger.error(f"Error creating experiment: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def start_experiment(self, experiment_name: str) -> Dict[str, Any]:
        """Start an experiment"""
        try:
            async with get_db_session() as session:
                stmt = select(ABExperiment).where(
                    ABExperiment.experiment_name == experiment_name
                )
                result = await session.execute(stmt)
                experiment = result.scalar_one_or_none()
                
                if not experiment:
                    return {
                        "status": "error",
                        "error": "Experiment not found",
                    }
                
                experiment.status = "active"
                experiment.start_date = datetime.now()
                await session.commit()
                
                logger.info(f"Started experiment: {experiment_name}")
                
                return {
                    "status": "success",
                    "experiment_name": experiment_name,
                }
                
        except Exception as e:
            logger.error(f"Error starting experiment: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def get_variant(
        self,
        experiment_name: str,
        wallet_address: str
    ) -> str:
        """
        Get variant assignment for a user (deterministic)
        
        Returns:
            "A" or "B"
        """
        try:
            async with get_db_session() as session:
                # Get experiment
                stmt = select(ABExperiment).where(
                    ABExperiment.experiment_name == experiment_name,
                    ABExperiment.status == "active"
                )
                result = await session.execute(stmt)
                experiment = result.scalar_one_or_none()
                
                if not experiment:
                    return "A"  # Default to variant A if experiment not found
                
                # Check existing allocation
                stmt = select(ABAllocation).where(
                    and_(
                        ABAllocation.experiment_id == experiment.id,
                        ABAllocation.wallet_address == wallet_address
                    )
                )
                result = await session.execute(stmt)
                allocation = result.scalar_one_or_none()
                
                if allocation:
                    return allocation.variant
                
                # Deterministic allocation based on address hash
                hash_input = f"{experiment_name}:{wallet_address}"
                hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
                allocation_ratio = float(experiment.allocation_ratio)
                
                variant = "B" if (hash_value % 100) < (allocation_ratio * 100) else "A"
                
                # Store allocation
                allocation = ABAllocation(
                    experiment_id=experiment.id,
                    wallet_address=wallet_address,
                    variant=variant
                )
                session.add(allocation)
                await session.commit()
                
                logger.debug(f"Allocated {wallet_address} to variant {variant} in {experiment_name}")
                
                return variant
                
        except Exception as e:
            logger.error(f"Error getting variant: {e}", exc_info=True)
            return "A"  # Default to variant A on error
    
    async def record_metric(
        self,
        experiment_name: str,
        wallet_address: str,
        metric_name: str,
        metric_value: Optional[float] = None,
        metric_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record a metric for an experiment"""
        try:
            async with get_db_session() as session:
                # Get experiment
                stmt = select(ABExperiment).where(
                    ABExperiment.experiment_name == experiment_name
                )
                result = await session.execute(stmt)
                experiment = result.scalar_one_or_none()
                
                if not experiment:
                    return False
                
                # Get variant
                variant = await self.get_variant(experiment_name, wallet_address)
                
                # Record metric
                metric = ABMetric(
                    experiment_id=experiment.id,
                    wallet_address=wallet_address,
                    variant=variant,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    metric_data=metric_data
                )
                
                session.add(metric)
                await session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error recording metric: {e}", exc_info=True)
            return False
    
    async def get_experiment_results(
        self,
        experiment_name: str
    ) -> Dict[str, Any]:
        """Get experiment results with statistical analysis"""
        try:
            async with get_db_session() as session:
                # Get experiment
                stmt = select(ABExperiment).where(
                    ABExperiment.experiment_name == experiment_name
                )
                result = await session.execute(stmt)
                experiment = result.scalar_one_or_none()
                
                if not experiment:
                    return {
                        "status": "error",
                        "error": "Experiment not found",
                    }
                
                # Get metrics
                stmt = select(ABMetric).where(
                    ABMetric.experiment_id == experiment.id
                )
                result = await session.execute(stmt)
                metrics = list(result.scalars().all())
                
                # Group by variant
                variant_a_metrics = [m for m in metrics if m.variant == "A"]
                variant_b_metrics = [m for m in metrics if m.variant == "B"]
                
                # Calculate statistics
                results = {
                    "experiment_name": experiment_name,
                    "status": experiment.status,
                    "variant_a": {
                        "name": experiment.variant_a_name,
                        "count": len(variant_a_metrics),
                    },
                    "variant_b": {
                        "name": experiment.variant_b_name,
                        "count": len(variant_b_metrics),
                    },
                }
                
                # Calculate metric statistics if numeric values exist
                metric_values_a = [m.metric_value for m in variant_a_metrics if m.metric_value is not None]
                metric_values_b = [m.metric_value for m in variant_b_metrics if m.metric_value is not None]
                
                if metric_values_a and metric_values_b:
                    mean_a = statistics.mean(metric_values_a)
                    mean_b = statistics.mean(metric_values_b)
                    
                    results["variant_a"]["mean"] = float(mean_a)
                    results["variant_b"]["mean"] = float(mean_b)
                    
                    # Calculate p-value (simplified t-test)
                    if len(metric_values_a) > 1 and len(metric_values_b) > 1:
                        std_a = statistics.stdev(metric_values_a)
                        std_b = statistics.stdev(metric_values_b)
                        
                        # Simplified statistical test
                        diff = abs(mean_a - mean_b)
                        pooled_std = ((std_a ** 2 + std_b ** 2) / 2) ** 0.5
                        
                        if pooled_std > 0:
                            t_stat = diff / pooled_std
                            # Simplified p-value (would use proper t-test in production)
                            p_value = max(0.0, min(1.0, 1.0 - (t_stat / 3.0)))
                        else:
                            p_value = 1.0
                        
                        results["statistical_significance"] = {
                            "p_value": float(p_value),
                            "significant": p_value < 0.05,
                        }
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting experiment results: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def list_experiments(self) -> List[Dict[str, Any]]:
        """List all experiments"""
        try:
            async with get_db_session() as session:
                stmt = select(ABExperiment)
                result = await session.execute(stmt)
                experiments = result.scalars().all()
                
                return [
                    {
                        "id": exp.id,
                        "name": exp.experiment_name,
                        "status": exp.status,
                        "variant_a": exp.variant_a_name,
                        "variant_b": exp.variant_b_name,
                        "created_at": exp.created_at.isoformat() if exp.created_at else None,
                    }
                    for exp in experiments
                ]
        except Exception as e:
            logger.error(f"Error listing experiments: {e}", exc_info=True)
            return []


"""
Industry benchmark service for comparing wallets to industry standards
"""
from typing import Dict, List, Optional, Any
from utils.logger import get_logger
from services.scoring import ScoringService
from services.industry_classifier import IndustryClassifier
from database.connection import get_session
from database.models import Score, IndustryProfile
from sqlalchemy import select, func

logger = get_logger(__name__)


class BenchmarkService:
    """Service for industry benchmarks"""
    
    # Industry categories
    INDUSTRIES = ['defi', 'nft', 'gaming', 'dao', 'mixed']
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.industry_classifier = IndustryClassifier()
    
    async def get_industry_benchmarks(
        self,
        industry: str = 'defi',
        session=None
    ) -> Dict[str, Any]:
        """
        Get benchmarks for industry
        
        Args:
            industry: Industry category
            session: Database session (optional)
            
        Returns:
            Benchmark dict
        """
        try:
            if industry not in self.INDUSTRIES:
                industry = 'defi'
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_industry_benchmarks(industry, db_session)
            else:
                return await self._get_industry_benchmarks(industry, session)
        except Exception as e:
            logger.error(f"Error getting industry benchmarks: {e}", exc_info=True)
            return {
                "industry": industry,
                "error": str(e),
            }
    
    async def _get_industry_benchmarks(
        self,
        industry: str,
        session
    ) -> Dict[str, Any]:
        """Get benchmarks from database"""
        try:
            # Get all wallets in this industry
            result = await session.execute(
                select(IndustryProfile, Score)
                .join(Score, IndustryProfile.wallet_address == Score.wallet_address)
                .where(IndustryProfile.industry_category == industry)
            )
            industry_scores = result.all()
            
            if not industry_scores:
                # Return default benchmarks if no data
                return {
                    "industry": industry,
                    "average_score": 500,
                    "median_score": 500,
                    "score_distribution": {
                        "0-200": 0,
                        "201-400": 0,
                        "401-600": 0,
                        "601-800": 0,
                        "801-1000": 0,
                    },
                    "risk_band_distribution": {
                        "1": 0,
                        "2": 0,
                        "3": 0,
                    },
                    "sample_size": 0,
                }
            
            scores = [s.score for _, s in industry_scores]
            risk_bands = [s.riskBand for _, s in industry_scores]
            
            # Calculate statistics
            avg_score = sum(scores) / len(scores) if scores else 0
            sorted_scores = sorted(scores)
            median_score = sorted_scores[len(sorted_scores) // 2] if sorted_scores else 0
            
            # Score distribution
            score_distribution = {
                "0-200": len([s for s in scores if 0 <= s <= 200]),
                "201-400": len([s for s in scores if 201 <= s <= 400]),
                "401-600": len([s for s in scores if 401 <= s <= 600]),
                "601-800": len([s for s in scores if 601 <= s <= 800]),
                "801-1000": len([s for s in scores if 801 <= s <= 1000]),
            }
            
            # Risk band distribution
            risk_band_distribution = {
                "1": len([r for r in risk_bands if r == 1]),
                "2": len([r for r in risk_bands if r == 2]),
                "3": len([r for r in risk_bands if r == 3]),
            }
            
            return {
                "industry": industry,
                "average_score": avg_score,
                "median_score": median_score,
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "score_distribution": score_distribution,
                "risk_band_distribution": risk_band_distribution,
                "sample_size": len(scores),
            }
        except Exception as e:
            logger.error(f"Error in _get_industry_benchmarks: {e}", exc_info=True)
            return {
                "industry": industry,
                "error": str(e),
            }
    
    async def compare_to_benchmark(
        self,
        address: str,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare wallet to benchmark
        
        Args:
            address: Wallet address
            industry: Optional industry (will auto-detect if not provided)
            
        Returns:
            Comparison dict
        """
        try:
            # Get wallet score
            score_info = await self.scoring_service.compute_score(address)
            wallet_score = score_info.get('score', 0)
            wallet_risk_band = score_info.get('riskBand', 0)
            
            # Auto-detect industry if not provided
            if not industry:
                industry_profile = await self.industry_classifier.classify_wallet(address)
                industry = industry_profile.get('industry_category', 'defi') if industry_profile else 'defi'
            
            # Get benchmarks
            benchmarks = await self.get_industry_benchmarks(industry)
            
            avg_score = benchmarks.get('average_score', 500)
            median_score = benchmarks.get('median_score', 500)
            
            # Calculate comparison
            vs_average = wallet_score - avg_score
            vs_median = wallet_score - median_score
            
            percentile = self._calculate_percentile(
                wallet_score,
                benchmarks.get('score_distribution', {}),
                benchmarks.get('sample_size', 0)
            )
            
            return {
                "address": address,
                "industry": industry,
                "wallet_score": wallet_score,
                "wallet_risk_band": wallet_risk_band,
                "benchmark": {
                    "average_score": avg_score,
                    "median_score": median_score,
                },
                "comparison": {
                    "vs_average": vs_average,
                    "vs_median": vs_median,
                    "percentile": percentile,
                },
                "benchmark_data": benchmarks,
            }
        except Exception as e:
            logger.error(f"Error comparing to benchmark: {e}", exc_info=True)
            return {
                "address": address,
                "error": str(e),
            }
    
    async def get_benchmark_percentiles(
        self,
        industry: str = 'defi',
        session=None
    ) -> Dict[str, Any]:
        """
        Get benchmark percentiles
        
        Args:
            industry: Industry category
            session: Database session (optional)
            
        Returns:
            Percentile dict
        """
        try:
            benchmarks = await self.get_industry_benchmarks(industry, session)
            
            # Calculate percentiles from distribution
            distribution = benchmarks.get('score_distribution', {})
            total = benchmarks.get('sample_size', 0)
            
            if total == 0:
                return {
                    "industry": industry,
                    "percentiles": {},
                }
            
            percentiles = {}
            cumulative = 0
            
            for range_key, count in distribution.items():
                cumulative += count
                percentile = (cumulative / total) * 100 if total > 0 else 0
                percentiles[range_key] = percentile
            
            return {
                "industry": industry,
                "percentiles": percentiles,
                "sample_size": total,
            }
        except Exception as e:
            logger.error(f"Error getting benchmark percentiles: {e}", exc_info=True)
            return {
                "industry": industry,
                "error": str(e),
            }
    
    async def update_benchmarks(
        self,
        industry: Optional[str] = None,
        session=None
    ) -> bool:
        """
        Update benchmark data
        
        Args:
            industry: Optional industry (updates all if None)
            session: Database session (optional)
            
        Returns:
            True if updated successfully
        """
        try:
            # In production, would recalculate and cache benchmarks
            # For now, benchmarks are calculated on-demand
            logger.info(f"Benchmark update requested for industry: {industry or 'all'}")
            return True
        except Exception as e:
            logger.error(f"Error updating benchmarks: {e}", exc_info=True)
            return False
    
    def _calculate_percentile(
        self,
        score: int,
        distribution: Dict[str, int],
        total: int
    ) -> float:
        """Calculate percentile from distribution"""
        if total == 0:
            return 0.0
        
        cumulative = 0
        for range_key, count in sorted(distribution.items()):
            # Parse range
            if '-' in range_key:
                min_val, max_val = map(int, range_key.split('-'))
                if min_val <= score <= max_val:
                    # Score is in this range
                    cumulative += (score - min_val) / (max_val - min_val + 1) * count
                    break
                elif score > max_val:
                    cumulative += count
            else:
                # Handle edge cases
                cumulative += count
        
        return (cumulative / total) * 100 if total > 0 else 0.0


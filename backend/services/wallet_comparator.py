"""
Wallet comparator for comparing wallets and finding similar ones
"""
from typing import Dict, List, Optional, Any
from utils.logger import get_logger
from services.scoring import ScoringService
from services.portfolio_service import PortfolioService
from database.connection import get_session
from database.models import Score
from sqlalchemy import select, func, and_

logger = get_logger(__name__)


class WalletComparator:
    """Service for comparing wallets"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.portfolio_service = PortfolioService()
    
    async def find_similar_wallets(
        self,
        address: str,
        criteria: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Find similar wallets
        
        Args:
            address: Wallet address
            criteria: Optional comparison criteria
            limit: Maximum number of similar wallets to return
            session: Database session (optional)
            
        Returns:
            List of similar wallet dicts
        """
        try:
            # Get target wallet data
            target_score_info = await self.scoring_service.compute_score(address)
            target_score = target_score_info.get('score', 0)
            target_risk_band = target_score_info.get('riskBand', 0)
            
            target_portfolio = await self.portfolio_service.get_total_portfolio_value(address)
            target_tx_summary = await self.portfolio_service.get_transaction_summary(address)
            
            # Default criteria
            score_range = criteria.get('score_range', 50) if criteria else 50
            portfolio_range = criteria.get('portfolio_range', 0.5) if criteria else 0.5  # 50% variance
            
            if session is None:
                async with get_session() as db_session:
                    return await self._find_similar_wallets(
                        address, target_score, target_risk_band, target_portfolio,
                        score_range, portfolio_range, limit, db_session
                    )
            else:
                return await self._find_similar_wallets(
                    address, target_score, target_risk_band, target_portfolio,
                    score_range, portfolio_range, limit, session
                )
        except Exception as e:
            logger.error(f"Error finding similar wallets: {e}", exc_info=True)
            return []
    
    async def _find_similar_wallets(
        self,
        address: str,
        target_score: int,
        target_risk_band: int,
        target_portfolio: float,
        score_range: int,
        portfolio_range: float,
        limit: int,
        session
    ) -> List[Dict[str, Any]]:
        """Find similar wallets from database"""
        try:
            # Find wallets with similar scores
            min_score = max(0, target_score - score_range)
            max_score = min(1000, target_score + score_range)
            
            result = await session.execute(
                select(Score).where(
                    and_(
                        Score.wallet_address != address,
                        Score.score >= min_score,
                        Score.score <= max_score,
                        Score.risk_band == target_risk_band
                    )
                ).order_by(func.abs(Score.score - target_score)).limit(limit * 2)  # Get more, filter later
            )
            candidates = result.scalars().all()
            
            similar_wallets = []
            for candidate in candidates:
                try:
                    # Get portfolio for comparison
                    candidate_portfolio = await self.portfolio_service.get_total_portfolio_value(
                        candidate.wallet_address
                    )
                    
                    # Check portfolio similarity
                    portfolio_diff = abs(candidate_portfolio - target_portfolio) / max(target_portfolio, 1)
                    if portfolio_diff > portfolio_range:
                        continue
                    
                    # Calculate similarity score
                    score_diff = abs(candidate.score - target_score)
                    similarity_score = 100 - (score_diff / score_range * 50) - (portfolio_diff / portfolio_range * 50)
                    similarity_score = max(0, min(100, similarity_score))
                    
                    similar_wallets.append({
                        "address": candidate.wallet_address,
                        "score": candidate.score,
                        "risk_band": candidate.risk_band,
                        "portfolio_value": candidate_portfolio,
                        "similarity_score": similarity_score,
                    })
                except Exception as e:
                    logger.warning(f"Error processing candidate {candidate.wallet_address}: {e}")
                    continue
            
            # Sort by similarity and limit
            similar_wallets.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_wallets[:limit]
        except Exception as e:
            logger.error(f"Error in _find_similar_wallets: {e}", exc_info=True)
            return []
    
    async def compare_wallets(
        self,
        address1: str,
        address2: str
    ) -> Dict[str, Any]:
        """
        Compare two wallets
        
        Args:
            address1: First wallet address
            address2: Second wallet address
            
        Returns:
            Comparison dict
        """
        try:
            # Get scores
            score1_info = await self.scoring_service.compute_score(address1)
            score2_info = await self.scoring_service.compute_score(address2)
            
            # Get portfolios
            portfolio1 = await self.portfolio_service.get_total_portfolio_value(address1)
            portfolio2 = await self.portfolio_service.get_total_portfolio_value(address2)
            
            # Get transaction summaries
            tx1 = await self.portfolio_service.get_transaction_summary(address1)
            tx2 = await self.portfolio_service.get_transaction_summary(address2)
            
            return {
                "address1": address1,
                "address2": address2,
                "comparison": {
                    "score": {
                        "address1": score1_info.get('score', 0),
                        "address2": score2_info.get('score', 0),
                        "difference": score1_info.get('score', 0) - score2_info.get('score', 0),
                    },
                    "risk_band": {
                        "address1": score1_info.get('riskBand', 0),
                        "address2": score2_info.get('riskBand', 0),
                    },
                    "portfolio": {
                        "address1": portfolio1,
                        "address2": portfolio2,
                        "difference": portfolio1 - portfolio2,
                    },
                    "transactions": {
                        "address1": {
                            "total": tx1.get('total_transactions', 0),
                            "volume": tx1.get('total_volume', 0),
                        },
                        "address2": {
                            "total": tx2.get('total_transactions', 0),
                            "volume": tx2.get('total_volume', 0),
                        },
                    },
                },
            }
        except Exception as e:
            logger.error(f"Error comparing wallets: {e}", exc_info=True)
            return {
                "address1": address1,
                "address2": address2,
                "error": str(e),
            }
    
    async def get_comparison_metrics(
        self,
        address: str,
        similar_wallets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get comparison metrics
        
        Args:
            address: Wallet address
            similar_wallets: List of similar wallet dicts
            
        Returns:
            Comparison metrics dict
        """
        try:
            if not similar_wallets:
                return {
                    "address": address,
                    "metrics": {},
                }
            
            scores = [w.get('score', 0) for w in similar_wallets]
            portfolios = [w.get('portfolio_value', 0) for w in similar_wallets]
            
            return {
                "address": address,
                "metrics": {
                    "score": {
                        "average": sum(scores) / len(scores) if scores else 0,
                        "median": sorted(scores)[len(scores) // 2] if scores else 0,
                        "min": min(scores) if scores else 0,
                        "max": max(scores) if scores else 0,
                    },
                    "portfolio": {
                        "average": sum(portfolios) / len(portfolios) if portfolios else 0,
                        "median": sorted(portfolios)[len(portfolios) // 2] if portfolios else 0,
                        "min": min(portfolios) if portfolios else 0,
                        "max": max(portfolios) if portfolios else 0,
                    },
                    "sample_size": len(similar_wallets),
                },
            }
        except Exception as e:
            logger.error(f"Error getting comparison metrics: {e}", exc_info=True)
            return {
                "address": address,
                "error": str(e),
            }
    
    async def get_percentile_rank(
        self,
        address: str,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Get percentile rank
        
        Args:
            address: Wallet address
            session: Database session (optional)
            
        Returns:
            Percentile rank dict
        """
        try:
            score_info = await self.scoring_service.compute_score(address)
            score = score_info.get('score', 0)
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_percentile_rank(address, score, db_session)
            else:
                return await self._get_percentile_rank(address, score, session)
        except Exception as e:
            logger.error(f"Error getting percentile rank: {e}", exc_info=True)
            return None
    
    async def _get_percentile_rank(
        self,
        address: str,
        score: int,
        session
    ) -> Optional[Dict[str, Any]]:
        """Get percentile rank from database"""
        try:
            # Get total count
            total_result = await session.execute(
                select(func.count(Score.wallet_address))
            )
            total_count = total_result.scalar() or 0
            
            if total_count == 0:
                return {
                    "address": address,
                    "score": score,
                    "percentile": 0,
                    "rank": 0,
                    "total_users": 0,
                }
            
            # Get count of users with lower scores
            lower_result = await session.execute(
                select(func.count(Score.wallet_address)).where(Score.score < score)
            )
            lower_count = lower_result.scalar() or 0
            
            percentile = (lower_count / total_count) * 100
            
            # Get rank (1 = highest score)
            rank_result = await session.execute(
                select(func.count(Score.wallet_address)).where(Score.score > score)
            )
            rank = rank_result.scalar() or 0
            rank += 1  # 1-indexed
            
            return {
                "address": address,
                "score": score,
                "percentile": percentile,
                "rank": rank,
                "total_users": total_count,
            }
        except Exception as e:
            logger.error(f"Error in _get_percentile_rank: {e}", exc_info=True)
            return None


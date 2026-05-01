"""
Offer aggregator service for aggregating and ranking loan offers
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger
from services.loan_marketplace import LoanMarketplace

logger = get_logger(__name__)


class OfferAggregator:
    """Service for aggregating and ranking loan offers"""
    
    def __init__(self):
        self.marketplace = LoanMarketplace()
    
    async def aggregate_offers(
        self,
        borrower_address: str,
        amount: Decimal,
        term_days: int,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate matching offers for a borrower
        
        Args:
            borrower_address: Borrower address
            amount: Requested loan amount
            term_days: Desired term in days
            session: Database session (optional)
            
        Returns:
            List of matching offers
        """
        try:
            filters = {
                'amount_min': amount * Decimal('0.9'),  # Allow 10% variance
                'amount_max': amount * Decimal('1.1'),
                'term_days': term_days,
                'borrower_address': borrower_address,
            }
            
            offers = await self.marketplace.get_available_offers(filters, limit=50, session=session)
            
            # Filter to exact matches
            matching_offers = [
                offer for offer in offers
                if (Decimal(str(offer['amount_min'])) <= amount <= Decimal(str(offer['amount_max'])) and
                    offer['term_days_min'] <= term_days <= offer['term_days_max'])
            ]
            
            return matching_offers
        except Exception as e:
            logger.error(f"Error aggregating offers: {e}", exc_info=True)
            return []
    
    def rank_offers(
        self,
        offers: List[Dict[str, Any]],
        criteria: str = 'rate'
    ) -> List[Dict[str, Any]]:
        """
        Rank offers by criteria
        
        Args:
            offers: List of offers
            criteria: Ranking criteria ('rate', 'term', 'amount')
            
        Returns:
            Ranked list of offers
        """
        try:
            if criteria == 'rate':
                # Sort by interest rate (ascending - lower is better)
                return sorted(offers, key=lambda x: x.get('interest_rate', 100))
            elif criteria == 'term':
                # Sort by term (ascending - shorter is better)
                return sorted(offers, key=lambda x: x.get('term_days_min', 365))
            elif criteria == 'amount':
                # Sort by amount (descending - higher is better)
                return sorted(offers, key=lambda x: x.get('amount_max', 0), reverse=True)
            else:
                # Default: rate
                return sorted(offers, key=lambda x: x.get('interest_rate', 100))
        except Exception as e:
            logger.error(f"Error ranking offers: {e}", exc_info=True)
            return offers
    
    def filter_offers(
        self,
        offers: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter offers by criteria
        
        Args:
            offers: List of offers
            filters: Filter criteria
            
        Returns:
            Filtered list of offers
        """
        try:
            filtered = offers
            
            if 'max_interest_rate' in filters:
                max_rate = filters['max_interest_rate']
                filtered = [o for o in filtered if o.get('interest_rate', 100) <= max_rate]
            
            if 'min_amount' in filters:
                min_amount = filters['min_amount']
                filtered = [o for o in filtered if o.get('amount_max', 0) >= min_amount]
            
            if 'max_amount' in filters:
                max_amount = filters['max_amount']
                filtered = [o for o in filtered if o.get('amount_min', 0) <= max_amount]
            
            if 'term_days' in filters:
                term = filters['term_days']
                filtered = [
                    o for o in filtered
                    if o.get('term_days_min', 0) <= term <= o.get('term_days_max', 365)
                ]
            
            if 'collateral_required' in filters:
                collateral_req = filters['collateral_required']
                filtered = [o for o in filtered if o.get('collateral_required', False) == collateral_req]
            
            return filtered
        except Exception as e:
            logger.error(f"Error filtering offers: {e}", exc_info=True)
            return offers
    
    async def get_best_offers(
        self,
        borrower_address: str,
        amount: Decimal,
        limit: int = 5,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get best matching offers for a borrower
        
        Args:
            borrower_address: Borrower address
            amount: Requested amount
            limit: Maximum number of offers
            session: Database session (optional)
            
        Returns:
            List of best offers (ranked by rate)
        """
        try:
            # Get all matching offers
            offers = await self.aggregate_offers(
                borrower_address, amount, 30, session=session  # Default 30 days term
            )
            
            # Rank by interest rate
            ranked = self.rank_offers(offers, criteria='rate')
            
            # Return top N
            return ranked[:limit]
        except Exception as e:
            logger.error(f"Error getting best offers: {e}", exc_info=True)
            return []


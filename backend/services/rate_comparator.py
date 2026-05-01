"""
Rate comparator service for side-by-side loan offer comparison
"""
from typing import Dict, List, Any
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class RateComparator:
    """Service for comparing loan offers side-by-side"""
    
    async def compare_offers(
        self,
        offers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple offers side-by-side
        
        Args:
            offers: List of offer dicts
            
        Returns:
            List of offers with comparison metrics
        """
        try:
            if not offers:
                return []
            
            # Calculate comparison metrics for each offer
            compared_offers = []
            for offer in offers:
                metrics = await self._calculate_offer_metrics(offer)
                compared_offers.append({
                    **offer,
                    **metrics
                })
            
            # Sort by total cost (ascending)
            compared_offers.sort(key=lambda x: x.get('total_cost', float('inf')))
            
            return compared_offers
        except Exception as e:
            logger.error(f"Error comparing offers: {e}", exc_info=True)
            return offers
    
    async def calculate_total_cost(
        self,
        offer: Dict[str, Any],
        amount: Decimal,
        term_days: int
    ) -> Decimal:
        """
        Calculate total repayment cost for an offer
        
        Args:
            offer: Offer dict
            amount: Loan amount
            term_days: Loan term in days
            
        Returns:
            Total repayment amount
        """
        try:
            interest_rate = Decimal(str(offer.get('interest_rate', 0)))
            principal = Decimal(str(amount))
            
            # Simple interest calculation: principal * (1 + rate * days / 365)
            interest = principal * interest_rate / Decimal('100') * Decimal(str(term_days)) / Decimal('365')
            total_cost = principal + interest
            
            return total_cost
        except Exception as e:
            logger.error(f"Error calculating total cost: {e}", exc_info=True)
            return Decimal('0')
    
    def calculate_apr(
        self,
        offer: Dict[str, Any]
    ) -> float:
        """
        Calculate effective APR for an offer
        
        Args:
            offer: Offer dict
            
        Returns:
            Effective APR percentage
        """
        try:
            # For now, APR is the same as interest_rate
            # In a more complex system, this would account for fees, compounding, etc.
            return float(offer.get('interest_rate', 0))
        except Exception as e:
            logger.error(f"Error calculating APR: {e}", exc_info=True)
            return 0.0
    
    async def generate_comparison_matrix(
        self,
        offers: List[Dict[str, Any]],
        amount: Decimal,
        term_days: int
    ) -> Dict[str, Any]:
        """
        Generate comparison matrix for multiple offers
        
        Args:
            offers: List of offer dicts
            amount: Loan amount to compare
            term_days: Loan term in days
            
        Returns:
            Comparison matrix dict
        """
        try:
            if not offers:
                return {
                    "offers": [],
                    "best_offer": None,
                    "metrics": {}
                }
            
            # Calculate metrics for each offer
            compared_offers = []
            for offer in offers:
                total_cost = await self.calculate_total_cost(offer, amount, term_days)
                apr = self.calculate_apr(offer)
                
                compared_offers.append({
                    "id": offer.get('id'),
                    "lender_address": offer.get('lender_address'),
                    "interest_rate": offer.get('interest_rate'),
                    "apr": apr,
                    "amount_min": float(offer.get('amount_min', 0)),
                    "amount_max": float(offer.get('amount_max', 0)),
                    "term_days_min": offer.get('term_days_min'),
                    "term_days_max": offer.get('term_days_max'),
                    "total_cost": float(total_cost),
                    "total_interest": float(total_cost - amount),
                    "collateral_required": offer.get('collateral_required', False),
                })
            
            # Find best offer (lowest total cost)
            best_offer = min(compared_offers, key=lambda x: x['total_cost'])
            
            # Calculate statistics
            interest_rates = [o['interest_rate'] for o in compared_offers]
            total_costs = [o['total_cost'] for o in compared_offers]
            
            metrics = {
                "avg_interest_rate": sum(interest_rates) / len(interest_rates) if interest_rates else 0,
                "min_interest_rate": min(interest_rates) if interest_rates else 0,
                "max_interest_rate": max(interest_rates) if interest_rates else 0,
                "avg_total_cost": sum(total_costs) / len(total_costs) if total_costs else 0,
                "min_total_cost": min(total_costs) if total_costs else 0,
                "max_total_cost": max(total_costs) if total_costs else 0,
                "savings_vs_avg": float(best_offer['total_cost'] - (sum(total_costs) / len(total_costs))) if total_costs else 0,
            }
            
            return {
                "offers": compared_offers,
                "best_offer": best_offer,
                "metrics": metrics,
                "comparison_amount": float(amount),
                "comparison_term_days": term_days,
            }
        except Exception as e:
            logger.error(f"Error generating comparison matrix: {e}", exc_info=True)
            return {
                "offers": [],
                "best_offer": None,
                "metrics": {}
            }
    
    async def _calculate_offer_metrics(
        self,
        offer: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate additional metrics for an offer
        
        Args:
            offer: Offer dict
            
        Returns:
            Metrics dict
        """
        try:
            apr = self.calculate_apr(offer)
            
            # Calculate monthly payment (simplified)
            amount_avg = (Decimal(str(offer.get('amount_min', 0))) + Decimal(str(offer.get('amount_max', 0)))) / 2
            term_avg = (offer.get('term_days_min', 0) + offer.get('term_days_max', 0)) / 2
            
            if term_avg > 0:
                monthly_rate = Decimal(str(apr)) / Decimal('100') / Decimal('12')
                months = Decimal(str(term_avg)) / Decimal('30')
                
                if monthly_rate > 0:
                    monthly_payment = amount_avg * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
                else:
                    monthly_payment = amount_avg / months
            else:
                monthly_payment = Decimal('0')
            
            return {
                "apr": apr,
                "monthly_payment": float(monthly_payment),
                "flexibility_score": self._calculate_flexibility_score(offer),
            }
        except Exception as e:
            logger.error(f"Error calculating offer metrics: {e}", exc_info=True)
            return {
                "apr": 0.0,
                "monthly_payment": 0.0,
                "flexibility_score": 0,
            }
    
    def _calculate_flexibility_score(self, offer: Dict[str, Any]) -> int:
        """
        Calculate flexibility score (0-100) based on offer terms
        
        Args:
            offer: Offer dict
            
        Returns:
            Flexibility score
        """
        try:
            score = 0
            
            # Amount range flexibility
            amount_min = Decimal(str(offer.get('amount_min', 0)))
            amount_max = Decimal(str(offer.get('amount_max', 0)))
            if amount_max > amount_min:
                range_ratio = float((amount_max - amount_min) / amount_max)
                score += int(range_ratio * 40)  # Up to 40 points
            
            # Term range flexibility
            term_min = offer.get('term_days_min', 0)
            term_max = offer.get('term_days_max', 0)
            if term_max > term_min:
                term_range_ratio = (term_max - term_min) / term_max if term_max > 0 else 0
                score += int(term_range_ratio * 30)  # Up to 30 points
            
            # Collateral flexibility
            if not offer.get('collateral_required', False):
                score += 30  # 30 points for no collateral requirement
            
            return min(100, score)
        except Exception as e:
            logger.error(f"Error calculating flexibility score: {e}", exc_info=True)
            return 0


"""
Quick loan service for mobile quick loan application
"""
from typing import Dict, List, Optional, Any
from utils.logger import get_logger
from services.loan_marketplace import LoanMarketplace
from services.loan_recommender import LoanRecommender
from services.scoring import ScoringService

logger = get_logger(__name__)


class QuickLoanService:
    """Service for quick loan application from mobile"""
    
    def __init__(self):
        self.loan_marketplace = LoanMarketplace()
        self.loan_recommender = LoanRecommender()
        self.scoring_service = ScoringService()
    
    async def create_quick_loan_request(
        self,
        address: str,
        amount: float,
        duration_days: int
    ) -> Optional[Dict[str, Any]]:
        """
        Create quick loan request
        
        Args:
            address: Wallet address
            amount: Loan amount requested
            duration_days: Loan duration in days
            
        Returns:
            Quick loan request dict
        """
        try:
            import uuid
            from datetime import datetime
            
            request_id = str(uuid.uuid4())
            
            # Get user score for recommendations
            score_info = await self.scoring_service.compute_score(address)
            score = score_info.get('score', 0)
            
            # Store request (in production, would save to database)
            request_data = {
                "request_id": request_id,
                "wallet_address": address,
                "amount": amount,
                "duration_days": duration_days,
                "score": score,
                "created_at": datetime.utcnow().isoformat(),
                "status": "pending",
            }
            
            logger.info(f"Created quick loan request {request_id} for {address}")
            
            return request_data
        except Exception as e:
            logger.error(f"Error creating quick loan request: {e}", exc_info=True)
            return None
    
    async def get_quick_loan_offers(
        self,
        address: str,
        request_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get AI-generated loan offers for quick loan request
        
        Args:
            address: Wallet address
            request_id: Quick loan request ID
            
        Returns:
            List of loan offer dicts
        """
        try:
            # Get recommendations from loan recommender
            recommendations = await self.loan_recommender.recommend_loans(
                address,
                amount=None,  # Will use request amount
                duration=None  # Will use request duration
            )
            
            # Get available offers from marketplace
            offers = await self.loan_marketplace.get_available_offers(
                address,
                limit=10
            )
            
            # Combine and format offers
            formatted_offers = []
            
            # Add recommended offers
            for rec in recommendations.get('recommendations', [])[:5]:
                formatted_offers.append({
                    "offer_id": rec.get('offer_id', f"rec_{len(formatted_offers)}"),
                    "lender_address": rec.get('lender_address', ''),
                    "amount": rec.get('amount', 0),
                    "interest_rate": rec.get('interest_rate', 0),
                    "duration_days": rec.get('duration_days', 0),
                    "collateral_required": rec.get('collateral_required', False),
                    "recommended": True,
                    "reason": rec.get('reason', 'AI recommended'),
                })
            
            # Add marketplace offers
            for offer in offers.get('offers', [])[:5]:
                formatted_offers.append({
                    "offer_id": offer.get('id', f"offer_{len(formatted_offers)}"),
                    "lender_address": offer.get('lender_address', ''),
                    "amount": offer.get('amount', 0),
                    "interest_rate": offer.get('interest_rate', 0),
                    "duration_days": offer.get('duration_days', 0),
                    "collateral_required": offer.get('collateral_required', False),
                    "recommended": False,
                })
            
            # Sort by interest rate (lowest first)
            formatted_offers.sort(key=lambda x: x.get('interest_rate', 999))
            
            return formatted_offers[:5]  # Return top 5 offers
        except Exception as e:
            logger.error(f"Error getting quick loan offers: {e}", exc_info=True)
            return []
    
    async def accept_quick_loan(
        self,
        address: str,
        offer_id: str,
        request_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Accept quick loan offer
        
        Args:
            address: Wallet address
            offer_id: Loan offer ID
            request_id: Optional quick loan request ID
            
        Returns:
            Loan creation result dict
        """
        try:
            # Accept offer via loan marketplace
            result = await self.loan_marketplace.accept_offer(
                address,
                offer_id
            )
            
            if result:
                logger.info(f"Quick loan accepted: offer {offer_id} by {address}")
                return {
                    "success": True,
                    "loan_id": result.get('loan_id'),
                    "offer_id": offer_id,
                    "message": "Loan created successfully",
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to accept loan offer",
                }
        except Exception as e:
            logger.error(f"Error accepting quick loan: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e),
            }
    
    async def get_quick_loan_status(
        self,
        address: str,
        loan_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get quick loan status
        
        Args:
            address: Wallet address
            loan_id: Loan ID
            
        Returns:
            Loan status dict
        """
        try:
            from services.loan_service import LoanService
            
            loan_service = LoanService()
            loans = await loan_service.get_loans_by_user(address)
            
            # Find loan by ID
            loan = next((l for l in loans if str(l.get('id')) == str(loan_id)), None)
            
            if not loan:
                return None
            
            return {
                "loan_id": loan_id,
                "status": loan.get('status', 'unknown'),
                "amount": loan.get('amount', 0),
                "interest_rate": loan.get('interest_rate', 0),
                "duration_days": loan.get('duration_days', 0),
                "created_at": loan.get('created_at'),
                "due_date": loan.get('due_date'),
            }
        except Exception as e:
            logger.error(f"Error getting quick loan status: {e}", exc_info=True)
            return None


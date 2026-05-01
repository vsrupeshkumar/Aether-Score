"""
Auction engine service for managing auction-style loan requests
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class AuctionEngine:
    """Service for managing auction-style loan requests"""
    
    # Default auction duration
    DEFAULT_AUCTION_DURATION_HOURS = 24
    
    # Auto-extend if bid within last N minutes
    AUTO_EXTEND_THRESHOLD_MINUTES = 5
    
    async def create_auction(
        self,
        request_id: int,
        duration_hours: int = DEFAULT_AUCTION_DURATION_HOURS,
        session=None
    ) -> bool:
        """
        Create auction for a loan request
        
        Args:
            request_id: Loan request ID
            duration_hours: Auction duration in hours
            session: Database session (optional)
            
        Returns:
            True if auction created successfully
        """
        try:
            from database.connection import get_session
            from database.models import LoanRequest
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_auction(request_id, duration_hours, db_session)
            else:
                return await self._create_auction(request_id, duration_hours, session)
        except Exception as e:
            logger.error(f"Error creating auction: {e}", exc_info=True)
            return False
    
    async def _create_auction(
        self,
        request_id: int,
        duration_hours: int,
        session
    ) -> bool:
        """Create auction in database"""
        from database.models import LoanRequest
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(LoanRequest).where(LoanRequest.id == request_id)
            )
            request = result.scalar_one_or_none()
            
            if not request:
                logger.warning(f"Request not found: {request_id}")
                return False
            
            if request.request_type != 'auction':
                logger.warning(f"Request is not auction type: {request_id}")
                return False
            
            # Set auction end time
            request.auction_end_time = datetime.utcnow() + timedelta(hours=duration_hours)
            request.status = 'bidding'
            await session.commit()
            
            logger.info(f"Created auction for request {request_id}, ends at {request.auction_end_time}")
            return True
        except Exception as e:
            logger.error(f"Error in _create_auction: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def submit_bid(
        self,
        request_id: int,
        lender_address: str,
        offer_id: int,
        session=None
    ) -> bool:
        """
        Submit bid on auction request
        
        Args:
            request_id: Loan request ID
            lender_address: Lender address
            offer_id: Loan offer ID (bid)
            session: Database session (optional)
            
        Returns:
            True if bid submitted successfully
        """
        try:
            from database.connection import get_session
            from database.models import LoanRequest, LoanOffer
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._submit_bid(request_id, lender_address, offer_id, db_session)
            else:
                return await self._submit_bid(request_id, lender_address, offer_id, session)
        except Exception as e:
            logger.error(f"Error submitting bid: {e}", exc_info=True)
            return False
    
    async def _submit_bid(
        self,
        request_id: int,
        lender_address: str,
        offer_id: int,
        session
    ) -> bool:
        """Submit bid in database"""
        from database.models import LoanRequest, LoanOffer
        from sqlalchemy import select
        
        try:
            # Get request
            request_result = await session.execute(
                select(LoanRequest).where(LoanRequest.id == request_id)
            )
            request = request_result.scalar_one_or_none()
            
            if not request:
                logger.warning(f"Request not found: {request_id}")
                return False
            
            if request.status != 'bidding':
                logger.warning(f"Request not accepting bids: {request_id}")
                return False
            
            # Check if auction expired
            if request.auction_end_time and request.auction_end_time < datetime.utcnow():
                logger.warning(f"Auction expired: {request_id}")
                request.status = 'expired'
                await session.commit()
                return False
            
            # Get offer
            offer_result = await session.execute(
                select(LoanOffer).where(LoanOffer.id == offer_id)
            )
            offer = offer_result.scalar_one_or_none()
            
            if not offer:
                logger.warning(f"Offer not found: {offer_id}")
                return False
            
            if offer.lender_address.lower() != lender_address.lower():
                logger.warning(f"Offer not owned by lender: {offer_id}")
                return False
            
            # Check if offer matches request criteria
            if (Decimal(str(offer.amount_min)) > Decimal(str(request.amount)) or
                Decimal(str(offer.amount_max)) < Decimal(str(request.amount))):
                logger.warning(f"Offer amount doesn't match request: {offer_id}")
                return False
            
            if offer.interest_rate > request.max_interest_rate:
                logger.warning(f"Offer rate too high: {offer_id}")
                return False
            
            # Check if this is a better bid than current winning offer
            if request.winning_offer_id:
                winning_result = await session.execute(
                    select(LoanOffer).where(LoanOffer.id == request.winning_offer_id)
                )
                winning_offer = winning_result.scalar_one_or_none()
                
                if winning_offer and offer.interest_rate >= winning_offer.interest_rate:
                    logger.info(f"Bid not better than current winning bid: {offer_id}")
                    return False
            
            # Update winning offer
            request.winning_offer_id = offer_id
            request.updated_at = datetime.utcnow()
            
            # Auto-extend auction if bid near end
            if request.auction_end_time:
                time_remaining = request.auction_end_time - datetime.utcnow()
                if time_remaining.total_seconds() < self.AUTO_EXTEND_THRESHOLD_MINUTES * 60:
                    request.auction_end_time += timedelta(minutes=10)
                    logger.info(f"Auto-extended auction {request_id} by 10 minutes")
            
            await session.commit()
            
            logger.info(f"Submitted bid {offer_id} on request {request_id} by {lender_address}")
            return True
        except Exception as e:
            logger.error(f"Error in _submit_bid: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def get_winning_bid(
        self,
        request_id: int,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Get current winning bid for auction
        
        Args:
            request_id: Loan request ID
            session: Database session (optional)
            
        Returns:
            Winning offer dict or None
        """
        try:
            from database.connection import get_session
            from database.models import LoanRequest, LoanOffer
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_winning_bid(request_id, db_session)
            else:
                return await self._get_winning_bid(request_id, session)
        except Exception as e:
            logger.error(f"Error getting winning bid: {e}", exc_info=True)
            return None
    
    async def _get_winning_bid(
        self,
        request_id: int,
        session
    ) -> Optional[Dict[str, Any]]:
        """Get winning bid from database"""
        from database.models import LoanRequest, LoanOffer
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(LoanRequest).where(LoanRequest.id == request_id)
            )
            request = result.scalar_one_or_none()
            
            if not request or not request.winning_offer_id:
                return None
            
            offer_result = await session.execute(
                select(LoanOffer).where(LoanOffer.id == request.winning_offer_id)
            )
            offer = offer_result.scalar_one_or_none()
            
            if not offer:
                return None
            
            return {
                "id": offer.id,
                "lender_address": offer.lender_address,
                "interest_rate": float(offer.interest_rate),
                "amount_min": float(offer.amount_min),
                "amount_max": float(offer.amount_max),
                "term_days_min": offer.term_days_min,
                "term_days_max": offer.term_days_max,
            }
        except Exception as e:
            logger.error(f"Error in _get_winning_bid: {e}", exc_info=True)
            return None
    
    async def close_auction(
        self,
        request_id: int,
        session=None
    ) -> bool:
        """
        Close auction and select winner
        
        Args:
            request_id: Loan request ID
            session: Database session (optional)
            
        Returns:
            True if closed successfully
        """
        try:
            from database.connection import get_session
            from database.models import LoanRequest, LoanOffer
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._close_auction(request_id, db_session)
            else:
                return await self._close_auction(request_id, session)
        except Exception as e:
            logger.error(f"Error closing auction: {e}", exc_info=True)
            return False
    
    async def _close_auction(
        self,
        request_id: int,
        session
    ) -> bool:
        """Close auction in database"""
        from database.models import LoanRequest, LoanOffer
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(LoanRequest).where(LoanRequest.id == request_id)
            )
            request = result.scalar_one_or_none()
            
            if not request:
                return False
            
            if request.status != 'bidding':
                logger.warning(f"Request not in bidding status: {request_id}")
                return False
            
            # Check if auction ended
            if request.auction_end_time and request.auction_end_time > datetime.utcnow():
                logger.warning(f"Auction not yet ended: {request_id}")
                return False
            
            if request.winning_offer_id:
                # Mark request as accepted
                request.status = 'accepted'
                
                # Mark winning offer as filled
                offer_result = await session.execute(
                    select(LoanOffer).where(LoanOffer.id == request.winning_offer_id)
                )
                offer = offer_result.scalar_one_or_none()
                if offer:
                    offer.status = 'filled'
            else:
                # No bids, mark as expired
                request.status = 'expired'
            
            request.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Closed auction {request_id}, winner: {request.winning_offer_id}")
            return True
        except Exception as e:
            logger.error(f"Error in _close_auction: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def extend_auction(
        self,
        request_id: int,
        additional_minutes: int = 10,
        session=None
    ) -> bool:
        """
        Extend auction duration
        
        Args:
            request_id: Loan request ID
            additional_minutes: Minutes to extend
            session: Database session (optional)
            
        Returns:
            True if extended successfully
        """
        try:
            from database.connection import get_session
            from database.models import LoanRequest
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._extend_auction(request_id, additional_minutes, db_session)
            else:
                return await self._extend_auction(request_id, additional_minutes, session)
        except Exception as e:
            logger.error(f"Error extending auction: {e}", exc_info=True)
            return False
    
    async def _extend_auction(
        self,
        request_id: int,
        additional_minutes: int,
        session
    ) -> bool:
        """Extend auction in database"""
        from database.models import LoanRequest
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(LoanRequest).where(LoanRequest.id == request_id)
            )
            request = result.scalar_one_or_none()
            
            if not request or not request.auction_end_time:
                return False
            
            request.auction_end_time += timedelta(minutes=additional_minutes)
            request.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Extended auction {request_id} by {additional_minutes} minutes")
            return True
        except Exception as e:
            logger.error(f"Error in _extend_auction: {e}", exc_info=True)
            await session.rollback()
            return False


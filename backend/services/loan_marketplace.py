"""
Loan marketplace service for managing loan offers and requests
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class LoanMarketplace:
    """Service for managing loan marketplace offers and requests"""
    
    async def create_offer(
        self,
        lender_address: str,
        amount_min: Decimal,
        amount_max: Decimal,
        interest_rate: Decimal,
        term_days_min: int,
        term_days_max: int,
        collateral_required: bool = False,
        accepted_collateral_tokens: Optional[List[str]] = None,
        ltv_ratio: Optional[Decimal] = None,
        expires_at: Optional[datetime] = None,
        borrower_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a loan offer
        
        Args:
            lender_address: Address of lender
            amount_min: Minimum loan amount
            amount_max: Maximum loan amount
            interest_rate: APR percentage
            term_days_min: Minimum term in days
            term_days_max: Maximum term in days
            collateral_required: Whether collateral is required
            accepted_collateral_tokens: List of accepted token addresses
            ltv_ratio: Loan-to-value ratio
            expires_at: Expiration date
            borrower_address: Optional targeted borrower
            metadata: Additional terms
            session: Database session (optional)
            
        Returns:
            Created offer dict
        """
        try:
            from database.connection import get_session
            from database.models import LoanOffer
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_offer(
                        lender_address, amount_min, amount_max, interest_rate,
                        term_days_min, term_days_max, collateral_required,
                        accepted_collateral_tokens, ltv_ratio, expires_at,
                        borrower_address, metadata, db_session
                    )
            else:
                return await self._create_offer(
                    lender_address, amount_min, amount_max, interest_rate,
                    term_days_min, term_days_max, collateral_required,
                    accepted_collateral_tokens, ltv_ratio, expires_at,
                    borrower_address, metadata, session
                )
        except Exception as e:
            logger.error(f"Error creating loan offer: {e}", exc_info=True)
            return None
    
    async def _create_offer(
        self,
        lender_address: str,
        amount_min: Decimal,
        amount_max: Decimal,
        interest_rate: Decimal,
        term_days_min: int,
        term_days_max: int,
        collateral_required: bool,
        accepted_collateral_tokens: Optional[List[str]],
        ltv_ratio: Optional[Decimal],
        expires_at: Optional[datetime],
        borrower_address: Optional[str],
        metadata: Optional[Dict[str, Any]],
        session
    ) -> Optional[Dict[str, Any]]:
        """Create offer in database"""
        from database.models import LoanOffer
        
        try:
            offer = LoanOffer(
                lender_address=lender_address,
                borrower_address=borrower_address,
                amount_min=amount_min,
                amount_max=amount_max,
                interest_rate=interest_rate,
                term_days_min=term_days_min,
                term_days_max=term_days_max,
                collateral_required=collateral_required,
                accepted_collateral_tokens=accepted_collateral_tokens or [],
                ltv_ratio=ltv_ratio,
                expires_at=expires_at,
                status='active',
                metadata=metadata or {}
            )
            session.add(offer)
            await session.commit()
            
            logger.info(f"Created loan offer {offer.id} by {lender_address}")
            
            return {
                "id": offer.id,
                "lender_address": lender_address,
                "borrower_address": borrower_address,
                "amount_min": float(amount_min),
                "amount_max": float(amount_max),
                "interest_rate": float(interest_rate),
                "term_days_min": term_days_min,
                "term_days_max": term_days_max,
                "status": offer.status,
                "created_at": offer.created_at.isoformat() if offer.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _create_offer: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def create_request(
        self,
        borrower_address: str,
        amount: Decimal,
        max_interest_rate: Decimal,
        term_days: int,
        collateral_amount: Optional[Decimal] = None,
        collateral_tokens: Optional[List[str]] = None,
        request_type: str = 'standard',
        auction_end_time: Optional[datetime] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a loan request
        
        Args:
            borrower_address: Address of borrower
            amount: Requested loan amount
            max_interest_rate: Maximum acceptable APR
            term_days: Desired term in days
            collateral_amount: Collateral amount if providing
            collateral_tokens: Available collateral tokens
            request_type: 'standard' or 'auction'
            auction_end_time: End time for auction
            session: Database session (optional)
            
        Returns:
            Created request dict
        """
        try:
            from database.connection import get_session
            from database.models import LoanRequest
            
            if session is None:
                async with get_session() as db_session:
                    return await self._create_request(
                        borrower_address, amount, max_interest_rate, term_days,
                        collateral_amount, collateral_tokens, request_type,
                        auction_end_time, db_session
                    )
            else:
                return await self._create_request(
                    borrower_address, amount, max_interest_rate, term_days,
                    collateral_amount, collateral_tokens, request_type,
                    auction_end_time, session
                )
        except Exception as e:
            logger.error(f"Error creating loan request: {e}", exc_info=True)
            return None
    
    async def _create_request(
        self,
        borrower_address: str,
        amount: Decimal,
        max_interest_rate: Decimal,
        term_days: int,
        collateral_amount: Optional[Decimal],
        collateral_tokens: Optional[List[str]],
        request_type: str,
        auction_end_time: Optional[datetime],
        session
    ) -> Optional[Dict[str, Any]]:
        """Create request in database"""
        from database.models import LoanRequest
        
        try:
            status = 'bidding' if request_type == 'auction' else 'open'
            
            request = LoanRequest(
                borrower_address=borrower_address,
                amount=amount,
                max_interest_rate=max_interest_rate,
                term_days=term_days,
                collateral_amount=collateral_amount,
                collateral_tokens=collateral_tokens or [],
                request_type=request_type,
                auction_end_time=auction_end_time,
                status=status
            )
            session.add(request)
            await session.commit()
            
            logger.info(f"Created loan request {request.id} by {borrower_address}")
            
            return {
                "id": request.id,
                "borrower_address": borrower_address,
                "amount": float(amount),
                "max_interest_rate": float(max_interest_rate),
                "term_days": term_days,
                "request_type": request_type,
                "status": status,
                "created_at": request.created_at.isoformat() if request.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _create_request: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def get_available_offers(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get available loan offers with filters
        
        Args:
            filters: Filter criteria (amount, interest_rate, term, etc.)
            limit: Maximum number of offers
            session: Database session (optional)
            
        Returns:
            List of offer dicts
        """
        try:
            from database.connection import get_session
            from database.models import LoanOffer
            from sqlalchemy import select, and_
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_offers(filters, limit, db_session)
            else:
                return await self._get_offers(filters, limit, session)
        except Exception as e:
            logger.error(f"Error getting offers: {e}", exc_info=True)
            return []
    
    async def _get_offers(
        self,
        filters: Optional[Dict[str, Any]],
        limit: int,
        session
    ) -> List[Dict[str, Any]]:
        """Get offers from database"""
        from database.models import LoanOffer
        from sqlalchemy import select, and_
        from datetime import datetime
        
        try:
            query = select(LoanOffer).where(LoanOffer.status == 'active')
            
            # Apply filters
            if filters:
                if 'amount_min' in filters:
                    query = query.where(LoanOffer.amount_max >= filters['amount_min'])
                if 'amount_max' in filters:
                    query = query.where(LoanOffer.amount_min <= filters['amount_max'])
                if 'max_interest_rate' in filters:
                    query = query.where(LoanOffer.interest_rate <= filters['max_interest_rate'])
                if 'term_days' in filters:
                    query = query.where(
                        LoanOffer.term_days_min <= filters['term_days'],
                        LoanOffer.term_days_max >= filters['term_days']
                    )
                if 'borrower_address' in filters:
                    query = query.where(
                        (LoanOffer.borrower_address == filters['borrower_address']) |
                        (LoanOffer.borrower_address.is_(None))
                    )
            
            # Filter expired offers
            query = query.where(
                (LoanOffer.expires_at.is_(None)) |
                (LoanOffer.expires_at > datetime.utcnow())
            )
            
            query = query.order_by(LoanOffer.interest_rate.asc()).limit(limit)
            
            result = await session.execute(query)
            offers = result.scalars().all()
            
            return [
                {
                    "id": offer.id,
                    "lender_address": offer.lender_address,
                    "borrower_address": offer.borrower_address,
                    "amount_min": float(offer.amount_min),
                    "amount_max": float(offer.amount_max),
                    "interest_rate": float(offer.interest_rate),
                    "term_days_min": offer.term_days_min,
                    "term_days_max": offer.term_days_max,
                    "collateral_required": offer.collateral_required,
                    "status": offer.status,
                    "created_at": offer.created_at.isoformat() if offer.created_at else None,
                }
                for offer in offers
            ]
        except Exception as e:
            logger.error(f"Error in _get_offers: {e}", exc_info=True)
            return []
    
    async def get_open_requests(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        session=None
    ) -> List[Dict[str, Any]]:
        """
        Get open loan requests
        
        Args:
            filters: Filter criteria
            limit: Maximum number of requests
            session: Database session (optional)
            
        Returns:
            List of request dicts
        """
        try:
            from database.connection import get_session
            from database.models import LoanRequest
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_requests(filters, limit, db_session)
            else:
                return await self._get_requests(filters, limit, session)
        except Exception as e:
            logger.error(f"Error getting requests: {e}", exc_info=True)
            return []
    
    async def _get_requests(
        self,
        filters: Optional[Dict[str, Any]],
        limit: int,
        session
    ) -> List[Dict[str, Any]]:
        """Get requests from database"""
        from database.models import LoanRequest
        from sqlalchemy import select
        from datetime import datetime
        
        try:
            query = select(LoanRequest).where(
                LoanRequest.status.in_(['open', 'bidding'])
            )
            
            # Apply filters
            if filters:
                if 'amount_min' in filters:
                    query = query.where(LoanRequest.amount >= filters['amount_min'])
                if 'amount_max' in filters:
                    query = query.where(LoanRequest.amount <= filters['amount_max'])
                if 'max_interest_rate' in filters:
                    query = query.where(LoanRequest.max_interest_rate >= filters['max_interest_rate'])
            
            # Filter expired auctions
            query = query.where(
                (LoanRequest.auction_end_time.is_(None)) |
                (LoanRequest.auction_end_time > datetime.utcnow())
            )
            
            query = query.order_by(LoanRequest.created_at.desc()).limit(limit)
            
            result = await session.execute(query)
            requests = result.scalars().all()
            
            return [
                {
                    "id": request.id,
                    "borrower_address": request.borrower_address,
                    "amount": float(request.amount),
                    "max_interest_rate": float(request.max_interest_rate),
                    "term_days": request.term_days,
                    "request_type": request.request_type,
                    "status": request.status,
                    "created_at": request.created_at.isoformat() if request.created_at else None,
                }
                for request in requests
            ]
        except Exception as e:
            logger.error(f"Error in _get_requests: {e}", exc_info=True)
            return []
    
    async def accept_offer(
        self,
        offer_id: int,
        borrower_address: str,
        session=None
    ) -> bool:
        """
        Accept a loan offer
        
        Args:
            offer_id: Offer ID
            borrower_address: Borrower address
            session: Database session (optional)
            
        Returns:
            True if accepted successfully
        """
        try:
            from database.connection import get_session
            from database.models import LoanOffer
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._accept_offer(offer_id, borrower_address, db_session)
            else:
                return await self._accept_offer(offer_id, borrower_address, session)
        except Exception as e:
            logger.error(f"Error accepting offer: {e}", exc_info=True)
            return False
    
    async def _accept_offer(
        self,
        offer_id: int,
        borrower_address: str,
        session
    ) -> bool:
        """Accept offer in database"""
        from database.models import LoanOffer
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(LoanOffer).where(LoanOffer.id == offer_id)
            )
            offer = result.scalar_one_or_none()
            
            if not offer:
                logger.warning(f"Offer not found: {offer_id}")
                return False
            
            if offer.status != 'active':
                logger.warning(f"Offer not active: {offer_id}")
                return False
            
            # Check if targeted to specific borrower
            if offer.borrower_address and offer.borrower_address.lower() != borrower_address.lower():
                logger.warning(f"Offer not for this borrower: {offer_id}")
                return False
            
            # Mark as filled
            offer.status = 'filled'
            offer.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Accepted offer {offer_id} by {borrower_address}")
            return True
        except Exception as e:
            logger.error(f"Error in _accept_offer: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def cancel_offer(
        self,
        offer_id: int,
        lender_address: str,
        session=None
    ) -> bool:
        """
        Cancel a loan offer
        
        Args:
            offer_id: Offer ID
            lender_address: Lender address (for authorization)
            session: Database session (optional)
            
        Returns:
            True if cancelled successfully
        """
        try:
            from database.connection import get_session
            from database.models import LoanOffer
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._cancel_offer(offer_id, lender_address, db_session)
            else:
                return await self._cancel_offer(offer_id, lender_address, session)
        except Exception as e:
            logger.error(f"Error cancelling offer: {e}", exc_info=True)
            return False
    
    async def _cancel_offer(
        self,
        offer_id: int,
        lender_address: str,
        session
    ) -> bool:
        """Cancel offer in database"""
        from database.models import LoanOffer
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(LoanOffer).where(LoanOffer.id == offer_id)
            )
            offer = result.scalar_one_or_none()
            
            if not offer:
                return False
            
            if offer.lender_address.lower() != lender_address.lower():
                logger.warning(f"Unauthorized cancellation attempt: {offer_id}")
                return False
            
            if offer.status not in ['active', 'filled']:
                return False
            
            offer.status = 'cancelled'
            offer.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Cancelled offer {offer_id} by {lender_address}")
            return True
        except Exception as e:
            logger.error(f"Error in _cancel_offer: {e}", exc_info=True)
            await session.rollback()
            return False
    
    async def cancel_request(
        self,
        request_id: int,
        borrower_address: str,
        session=None
    ) -> bool:
        """
        Cancel a loan request
        
        Args:
            request_id: Request ID
            borrower_address: Borrower address (for authorization)
            session: Database session (optional)
            
        Returns:
            True if cancelled successfully
        """
        try:
            from database.connection import get_session
            from database.models import LoanRequest
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._cancel_request(request_id, borrower_address, db_session)
            else:
                return await self._cancel_request(request_id, borrower_address, session)
        except Exception as e:
            logger.error(f"Error cancelling request: {e}", exc_info=True)
            return False
    
    async def _cancel_request(
        self,
        request_id: int,
        borrower_address: str,
        session
    ) -> bool:
        """Cancel request in database"""
        from database.models import LoanRequest
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(LoanRequest).where(LoanRequest.id == request_id)
            )
            request = result.scalar_one_or_none()
            
            if not request:
                return False
            
            if request.borrower_address.lower() != borrower_address.lower():
                logger.warning(f"Unauthorized cancellation attempt: {request_id}")
                return False
            
            if request.status not in ['open', 'bidding']:
                return False
            
            request.status = 'cancelled'
            request.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Cancelled request {request_id} by {borrower_address}")
            return True
        except Exception as e:
            logger.error(f"Error in _cancel_request: {e}", exc_info=True)
            await session.rollback()
            return False


"""
Auto-negotiation service for automated loan negotiation
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from utils.logger import get_logger
from core.agent import NeuroLendAgent
from services.loan_recommender import LoanRecommender
from services.preference_manager import PreferenceManager
from services.loan_marketplace import LoanMarketplace
from services.auction_engine import AuctionEngine

logger = get_logger(__name__)


class AutoNegotiationService:
    """Service for managing automated loan negotiations"""
    
    # Negotiation timeout (hours)
    NEGOTIATION_TIMEOUT_HOURS = 24
    
    def __init__(self):
        self.agent = NeuroLendAgent()
        self.recommender = LoanRecommender()
        self.preference_manager = PreferenceManager()
        self.marketplace = LoanMarketplace()
        self.auction_engine = AuctionEngine()
    
    async def start_negotiation(
        self,
        address: str,
        loan_request: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Start auto-negotiation
        
        Args:
            address: Wallet address
            loan_request: Loan request details
            preferences: User preferences (optional)
            session: Database session (optional)
            
        Returns:
            Negotiation session dict
        """
        try:
            from database.connection import get_session
            from database.models import NegotiationSession, LoanRequest
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._start_negotiation(address, loan_request, preferences, db_session)
            else:
                return await self._start_negotiation(address, loan_request, preferences, session)
        except Exception as e:
            logger.error(f"Error starting negotiation: {e}", exc_info=True)
            return None
    
    async def _start_negotiation(
        self,
        address: str,
        loan_request: Dict[str, Any],
        preferences: Optional[Dict[str, Any]],
        session
    ) -> Optional[Dict[str, Any]]:
        """Start negotiation in database"""
        from database.models import NegotiationSession, LoanRequest
        from sqlalchemy import select
        
        try:
            # Get or create preferences
            if not preferences:
                preferences = await self.preference_manager.get_preferences(address, session)
            
            # Create loan request if needed
            loan_request_id = None
            if loan_request.get('create_request', False):
                created_request = await self.marketplace.create_request(
                    address,
                    Decimal(str(loan_request['amount'])),
                    Decimal(str(loan_request.get('max_interest_rate', 25))),
                    loan_request.get('term_days', 30),
                    None,  # collateral_amount
                    None,  # collateral_tokens
                    loan_request.get('request_type', 'standard'),
                    None,  # auction_end_time
                    session
                )
                if created_request:
                    loan_request_id = created_request.get('id')
            
            # Create negotiation session
            session_obj = NegotiationSession(
                wallet_address=address,
                loan_request_id=loan_request_id,
                preferences_id=address,  # Use wallet_address as FK
                status='active',
                negotiation_history=[{
                    "action": "started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "loan_request": loan_request,
                }]
            )
            session.add(session_obj)
            await session.commit()
            
            # Start negotiation process
            negotiation_result = await self.agent.auto_negotiate(address, loan_request, preferences)
            
            # Update session with initial results
            session_obj.negotiation_history.append({
                "action": "initial_search",
                "timestamp": datetime.utcnow().isoformat(),
                "result": negotiation_result,
            })
            
            if negotiation_result.get('accepted_offer'):
                session_obj.status = 'completed'
                session_obj.current_offer_id = negotiation_result['accepted_offer'].get('id')
            
            await session.commit()
            
            logger.info(f"Started negotiation session {session_obj.id} for {address}")
            
            return {
                "negotiation_id": session_obj.id,
                "status": session_obj.status,
                "result": negotiation_result,
                "created_at": session_obj.created_at.isoformat() if session_obj.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _start_negotiation: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def continue_negotiation(
        self,
        negotiation_id: int,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Continue ongoing negotiation
        
        Args:
            negotiation_id: Negotiation session ID
            session: Database session (optional)
            
        Returns:
            Updated negotiation status dict
        """
        try:
            from database.connection import get_session
            from database.models import NegotiationSession
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._continue_negotiation(negotiation_id, db_session)
            else:
                return await self._continue_negotiation(negotiation_id, session)
        except Exception as e:
            logger.error(f"Error continuing negotiation: {e}", exc_info=True)
            return None
    
    async def _continue_negotiation(
        self,
        negotiation_id: int,
        session
    ) -> Optional[Dict[str, Any]]:
        """Continue negotiation in database"""
        from database.models import NegotiationSession
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(NegotiationSession).where(NegotiationSession.id == negotiation_id)
            )
            negotiation = result.scalar_one_or_none()
            
            if not negotiation:
                return None
            
            if negotiation.status != 'active':
                return {
                    "negotiation_id": negotiation_id,
                    "status": negotiation.status,
                    "message": "Negotiation is not active",
                }
            
            # Check timeout
            if negotiation.created_at:
                elapsed = datetime.utcnow() - negotiation.created_at
                if elapsed.total_seconds() > self.NEGOTIATION_TIMEOUT_HOURS * 3600:
                    negotiation.status = 'expired'
                    await session.commit()
                    return {
                        "negotiation_id": negotiation_id,
                        "status": "expired",
                        "message": "Negotiation expired",
                    }
            
            # Get preferences
            preferences = await self.preference_manager.get_preferences(negotiation.wallet_address, session)
            
            # Get loan request if exists
            loan_request = None
            if negotiation.loan_request_id:
                from database.models import LoanRequest
                req_result = await session.execute(
                    select(LoanRequest).where(LoanRequest.id == negotiation.loan_request_id)
                )
                loan_request_obj = req_result.scalar_one_or_none()
                if loan_request_obj:
                    loan_request = {
                        "amount": float(loan_request_obj.amount),
                        "term_days": loan_request_obj.term_days,
                        "max_interest_rate": float(loan_request_obj.max_interest_rate),
                    }
            
            if not loan_request:
                # Use last negotiation history to reconstruct request
                history = negotiation.negotiation_history or []
                if history:
                    last_request = history[0].get('loan_request', {})
                    loan_request = last_request
            
            # Continue negotiation
            negotiation_result = await self.agent.auto_negotiate(
                negotiation.wallet_address,
                loan_request or {},
                preferences
            )
            
            # Update session
            negotiation.negotiation_history.append({
                "action": "continued",
                "timestamp": datetime.utcnow().isoformat(),
                "result": negotiation_result,
            })
            
            if negotiation_result.get('accepted_offer'):
                negotiation.status = 'completed'
                negotiation.current_offer_id = negotiation_result['accepted_offer'].get('id')
            
            negotiation.updated_at = datetime.utcnow()
            await session.commit()
            
            return {
                "negotiation_id": negotiation_id,
                "status": negotiation.status,
                "result": negotiation_result,
                "updated_at": negotiation.updated_at.isoformat() if negotiation.updated_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _continue_negotiation: {e}", exc_info=True)
            await session.rollback()
            return None
    
    async def get_negotiation_status(
        self,
        negotiation_id: int,
        session=None
    ) -> Optional[Dict[str, Any]]:
        """
        Get negotiation status
        
        Args:
            negotiation_id: Negotiation session ID
            session: Database session (optional)
            
        Returns:
            Negotiation status dict
        """
        try:
            from database.connection import get_session
            from database.models import NegotiationSession
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._get_negotiation_status(negotiation_id, db_session)
            else:
                return await self._get_negotiation_status(negotiation_id, session)
        except Exception as e:
            logger.error(f"Error getting negotiation status: {e}", exc_info=True)
            return None
    
    async def _get_negotiation_status(
        self,
        negotiation_id: int,
        session
    ) -> Optional[Dict[str, Any]]:
        """Get negotiation status from database"""
        from database.models import NegotiationSession
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(NegotiationSession).where(NegotiationSession.id == negotiation_id)
            )
            negotiation = result.scalar_one_or_none()
            
            if not negotiation:
                return None
            
            return {
                "negotiation_id": negotiation.id,
                "wallet_address": negotiation.wallet_address,
                "status": negotiation.status,
                "loan_request_id": negotiation.loan_request_id,
                "current_offer_id": negotiation.current_offer_id,
                "negotiation_history": negotiation.negotiation_history or [],
                "created_at": negotiation.created_at.isoformat() if negotiation.created_at else None,
                "updated_at": negotiation.updated_at.isoformat() if negotiation.updated_at else None,
            }
        except Exception as e:
            logger.error(f"Error in _get_negotiation_status: {e}", exc_info=True)
            return None
    
    async def cancel_negotiation(
        self,
        negotiation_id: int,
        address: str,
        session=None
    ) -> bool:
        """
        Cancel negotiation
        
        Args:
            negotiation_id: Negotiation session ID
            address: Wallet address (for authorization)
            session: Database session (optional)
            
        Returns:
            True if cancelled successfully
        """
        try:
            from database.connection import get_session
            from database.models import NegotiationSession
            from sqlalchemy import select
            
            if session is None:
                async with get_session() as db_session:
                    return await self._cancel_negotiation(negotiation_id, address, db_session)
            else:
                return await self._cancel_negotiation(negotiation_id, address, session)
        except Exception as e:
            logger.error(f"Error cancelling negotiation: {e}", exc_info=True)
            return False
    
    async def _cancel_negotiation(
        self,
        negotiation_id: int,
        address: str,
        session
    ) -> bool:
        """Cancel negotiation in database"""
        from database.models import NegotiationSession
        from sqlalchemy import select
        
        try:
            result = await session.execute(
                select(NegotiationSession).where(
                    NegotiationSession.id == negotiation_id,
                    NegotiationSession.wallet_address == address
                )
            )
            negotiation = result.scalar_one_or_none()
            
            if not negotiation:
                return False
            
            if negotiation.status not in ['active', 'completed']:
                return False
            
            negotiation.status = 'cancelled'
            negotiation.negotiation_history.append({
                "action": "cancelled",
                "timestamp": datetime.utcnow().isoformat(),
            })
            negotiation.updated_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Cancelled negotiation {negotiation_id} by {address}")
            return True
        except Exception as e:
            logger.error(f"Error in _cancel_negotiation: {e}", exc_info=True)
            await session.rollback()
            return False


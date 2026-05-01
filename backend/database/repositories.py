"""
Repository pattern for data access layer
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_
from sqlalchemy.orm import selectinload
from .models import (
    Score, ScoreHistory, UserData, BatchUpdate,
    User, Loan, LoanPayment, Transaction, GDPRRequest
)
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class ScoreRepository:
    """Repository for score data access"""
    
    @staticmethod
    async def get_score(session: AsyncSession, wallet_address: str) -> Optional[Score]:
        """Get score for a wallet address"""
        try:
            result = await session.execute(
                select(Score).where(Score.wallet_address == wallet_address)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting score: {e}", exc_info=True, extra={"address": wallet_address})
            return None
    
    @staticmethod
    async def upsert_score(
        session: AsyncSession,
        wallet_address: str,
        score: int,
        risk_band: int,
        computed_at: Optional[datetime] = None
    ) -> Score:
        """Insert or update score"""
        try:
            existing = await ScoreRepository.get_score(session, wallet_address)
            
            if existing:
                existing.score = score
                existing.risk_band = risk_band
                existing.last_updated = datetime.utcnow()
                existing.computed_at = computed_at or datetime.utcnow()
                return existing
            else:
                new_score = Score(
                    wallet_address=wallet_address,
                    score=score,
                    risk_band=risk_band,
                    last_updated=datetime.utcnow(),
                    computed_at=computed_at or datetime.utcnow()
                )
                session.add(new_score)
                return new_score
        except Exception as e:
            logger.error(f"Error upserting score: {e}", exc_info=True, extra={"address": wallet_address})
            raise
    
    @staticmethod
    async def get_scores_batch(
        session: AsyncSession,
        wallet_addresses: List[str],
        min_score: Optional[int] = None,
        max_score: Optional[int] = None
    ) -> List[Score]:
        """Get scores for multiple addresses"""
        try:
            query = select(Score).where(Score.wallet_address.in_(wallet_addresses))
            
            if min_score is not None:
                query = query.where(Score.score >= min_score)
            if max_score is not None:
                query = query.where(Score.score <= max_score)
            
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting scores batch: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_recent_scores(
        session: AsyncSession,
        limit: int = 100,
        hours: int = 24
    ) -> List[Score]:
        """Get recently updated scores"""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            result = await session.execute(
                select(Score)
                .where(Score.last_updated >= cutoff)
                .order_by(Score.last_updated.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting recent scores: {e}", exc_info=True)
            return []


class ScoreHistoryRepository:
    """Repository for score history data access"""
    
    @staticmethod
    async def add_history(
        session: AsyncSession,
        wallet_address: str,
        score: int,
        risk_band: int,
        previous_score: Optional[int] = None,
        explanation: Optional[str] = None,
        change_reason: Optional[str] = None,
        computed_at: Optional[datetime] = None
    ) -> ScoreHistory:
        """Add score history entry"""
        try:
            history = ScoreHistory(
                wallet_address=wallet_address,
                score=score,
                risk_band=risk_band,
                previous_score=previous_score,
                explanation=explanation,
                change_reason=change_reason,
                computed_at=computed_at or datetime.utcnow()
            )
            session.add(history)
            return history
        except Exception as e:
            logger.error(f"Error adding history: {e}", exc_info=True, extra={"address": wallet_address})
            raise
    
    @staticmethod
    async def get_history(
        session: AsyncSession,
        wallet_address: str,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ScoreHistory]:
        """Get score history for an address"""
        try:
            query = select(ScoreHistory).where(ScoreHistory.wallet_address == wallet_address)
            
            if start_date:
                query = query.where(ScoreHistory.computed_at >= start_date)
            if end_date:
                query = query.where(ScoreHistory.computed_at <= end_date)
            
            result = await session.execute(
                query
                .order_by(ScoreHistory.computed_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting history: {e}", exc_info=True, extra={"address": wallet_address})
            return []
    
    @staticmethod
    async def get_latest_score(
        session: AsyncSession,
        wallet_address: str
    ) -> Optional[ScoreHistory]:
        """Get latest score history entry"""
        try:
            result = await session.execute(
                select(ScoreHistory)
                .where(ScoreHistory.wallet_address == wallet_address)
                .order_by(ScoreHistory.computed_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting latest score: {e}", exc_info=True, extra={"address": wallet_address})
            return None
    
    @staticmethod
    async def cleanup_old_history(
        session: AsyncSession,
        days: int = 90
    ) -> int:
        """Delete history older than specified days"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = await session.execute(
                delete(ScoreHistory).where(ScoreHistory.computed_at < cutoff)
            )
            return result.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up history: {e}", exc_info=True)
            return 0


class UserDataRepository:
    """Repository for user data access"""
    
    @staticmethod
    async def get_user_data(session: AsyncSession, wallet_address: str) -> Optional[UserData]:
        """Get user data for a wallet address"""
        try:
            result = await session.execute(
                select(UserData).where(UserData.wallet_address == wallet_address)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user data: {e}", exc_info=True, extra={"address": wallet_address})
            return None
    
    @staticmethod
    async def upsert_user_data(
        session: AsyncSession,
        wallet_address: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserData:
        """Insert or update user data"""
        try:
            existing = await UserDataRepository.get_user_data(session, wallet_address)
            
            if existing:
                if metadata:
                    existing.tx_metadata = metadata
                existing.updated_at = datetime.utcnow()
                return existing
            else:
                new_data = UserData(
                    wallet_address=wallet_address,
                    metadata=metadata or {}
                )
                session.add(new_data)
                return new_data
        except Exception as e:
            logger.error(f"Error upserting user data: {e}", exc_info=True, extra={"address": wallet_address})
            raise


class BatchUpdateRepository:
    """Repository for batch update tracking"""
    
    @staticmethod
    async def create_batch(
        session: AsyncSession,
        batch_id: str,
        addresses: List[str]
    ) -> BatchUpdate:
        """Create a new batch update record"""
        try:
            batch = BatchUpdate(
                batch_id=batch_id,
                addresses=addresses,
                status="pending"
            )
            session.add(batch)
            return batch
        except Exception as e:
            logger.error(f"Error creating batch: {e}", exc_info=True, extra={"batch_id": batch_id})
            raise
    
    @staticmethod
    async def get_batch(session: AsyncSession, batch_id: str) -> Optional[BatchUpdate]:
        """Get batch update by ID"""
        try:
            result = await session.execute(
                select(BatchUpdate).where(BatchUpdate.batch_id == batch_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting batch: {e}", exc_info=True, extra={"batch_id": batch_id})
            return None
    
    @staticmethod
    async def update_batch_status(
        session: AsyncSession,
        batch_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Update batch status"""
        try:
            batch = await BatchUpdateRepository.get_batch(session, batch_id)
            if not batch:
                return False
            
            batch.status = status
            if status in ["completed", "failed"]:
                batch.completed_at = datetime.utcnow()
            if error_message:
                batch.error_message = error_message
            
            return True
        except Exception as e:
            logger.error(f"Error updating batch status: {e}", exc_info=True, extra={"batch_id": batch_id})
            return False


class UserRepository:
    """Repository for user data access"""
    
    @staticmethod
    async def get_user(session: AsyncSession, wallet_address: str) -> Optional[User]:
        """Get user by wallet address"""
        try:
            result = await session.execute(
                select(User).where(
                    User.wallet_address == wallet_address,
                    User.deleted_at.is_(None)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user: {e}", exc_info=True, extra={"address": wallet_address})
            return None
    
    @staticmethod
    async def create_user(
        session: AsyncSession,
        wallet_address: str,
        email: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> User:
        """Create a new user"""
        try:
            user = User(
                wallet_address=wallet_address,
                email=email,
                preferences=preferences or {}
            )
            session.add(user)
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True, extra={"address": wallet_address})
            raise
    
    @staticmethod
    async def update_gdpr_consent(
        session: AsyncSession,
        wallet_address: str,
        consent: bool
    ) -> bool:
        """Update GDPR consent"""
        try:
            user = await UserRepository.get_user(session, wallet_address)
            if not user:
                return False
            
            user.gdpr_consent = consent
            if consent:
                user.consent_date = datetime.utcnow()
            else:
                user.consent_date = None
            
            return True
        except Exception as e:
            logger.error(f"Error updating GDPR consent: {e}", exc_info=True, extra={"address": wallet_address})
            return False
    
    @staticmethod
    async def request_deletion(
        session: AsyncSession,
        wallet_address: str
    ) -> bool:
        """Request data deletion (soft delete)"""
        try:
            user = await UserRepository.get_user(session, wallet_address)
            if not user:
                return False
            
            user.data_deletion_requested = True
            user.deletion_requested_at = datetime.utcnow()
            
            return True
        except Exception as e:
            logger.error(f"Error requesting deletion: {e}", exc_info=True, extra={"address": wallet_address})
            return False


class LoanRepository:
    """Repository for loan data access"""
    
    @staticmethod
    async def create_loan(
        session: AsyncSession,
        wallet_address: str,
        loan_id: int,
        amount: Decimal,
        interest_rate: Decimal,
        term_days: int,
        status: str = "pending",
        collateral_amount: Optional[Decimal] = None,
        collateral_token: Optional[str] = None,
        tx_hash: Optional[str] = None
    ) -> Loan:
        """Create a new loan"""
        try:
            loan = Loan(
                wallet_address=wallet_address,
                loan_id=loan_id,
                amount=amount,
                interest_rate=interest_rate,
                term_days=term_days,
                status=status,
                collateral_amount=collateral_amount,
                collateral_token=collateral_token,
                tx_hash=tx_hash
            )
            session.add(loan)
            return loan
        except Exception as e:
            logger.error(f"Error creating loan: {e}", exc_info=True, extra={"address": wallet_address})
            raise
    
    @staticmethod
    async def get_loans_by_user(
        session: AsyncSession,
        wallet_address: str,
        status: Optional[str] = None
    ) -> List[Loan]:
        """Get loans for a user"""
        try:
            query = select(Loan).where(Loan.wallet_address == wallet_address)
            if status:
                query = query.where(Loan.status == status)
            
            result = await session.execute(query.order_by(Loan.created_at.desc()))
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting loans: {e}", exc_info=True, extra={"address": wallet_address})
            return []
    
    @staticmethod
    async def add_payment(
        session: AsyncSession,
        loan_id: int,
        amount: Decimal,
        payment_type: str,
        tx_hash: Optional[str] = None
    ) -> LoanPayment:
        """Add a loan payment"""
        try:
            payment = LoanPayment(
                loan_id=loan_id,
                amount=amount,
                payment_type=payment_type,
                tx_hash=tx_hash
            )
            session.add(payment)
            return payment
        except Exception as e:
            logger.error(f"Error adding payment: {e}", exc_info=True, extra={"loan_id": loan_id})
            raise


class TransactionRepository:
    """Repository for transaction data access"""
    
    @staticmethod
    async def create_transaction(
        session: AsyncSession,
        wallet_address: str,
        tx_hash: str,
        tx_type: str,
        block_number: Optional[int] = None,
        block_timestamp: Optional[datetime] = None,
        from_address: Optional[str] = None,
        to_address: Optional[str] = None,
        value: Optional[Decimal] = None,
        gas_used: Optional[int] = None,
        gas_price: Optional[int] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """Create a new transaction record"""
        try:
            transaction = Transaction(
                wallet_address=wallet_address,
                tx_hash=tx_hash,
                tx_type=tx_type,
                block_number=block_number,
                block_timestamp=block_timestamp,
                from_address=from_address,
                to_address=to_address,
                value=value,
                gas_used=gas_used,
                gas_price=gas_price,
                status=status,
                metadata=metadata or {}
            )
            session.add(transaction)
            return transaction
        except Exception as e:
            logger.error(f"Error creating transaction: {e}", exc_info=True, extra={"tx_hash": tx_hash})
            raise
    
    @staticmethod
    async def get_transactions_by_user(
        session: AsyncSession,
        wallet_address: str,
        tx_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions for a user"""
        try:
            query = select(Transaction).where(Transaction.wallet_address == wallet_address)
            if tx_type:
                query = query.where(Transaction.tx_type == tx_type)
            
            result = await session.execute(
                query.order_by(Transaction.block_timestamp.desc()).limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting transactions: {e}", exc_info=True, extra={"address": wallet_address})
            return []


class GDPRRepository:
    """Repository for GDPR request tracking"""
    
    @staticmethod
    async def create_request(
        session: AsyncSession,
        wallet_address: str,
        request_type: str
    ) -> GDPRRequest:
        """Create a GDPR request"""
        try:
            request = GDPRRequest(
                wallet_address=wallet_address,
                request_type=request_type,
                status="pending"
            )
            session.add(request)
            return request
        except Exception as e:
            logger.error(f"Error creating GDPR request: {e}", exc_info=True, extra={"address": wallet_address})
            raise
    
    @staticmethod
    async def get_request(
        session: AsyncSession,
        request_id: int
    ) -> Optional[GDPRRequest]:
        """Get GDPR request by ID"""
        try:
            result = await session.execute(
                select(GDPRRequest).where(GDPRRequest.id == request_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting GDPR request: {e}", exc_info=True, extra={"request_id": request_id})
            return None
    
    @staticmethod
    async def update_request_status(
        session: AsyncSession,
        request_id: int,
        status: str,
        export_file_path: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update GDPR request status"""
        try:
            request = await GDPRRepository.get_request(session, request_id)
            if not request:
                return False
            
            request.status = status
            if status == "completed":
                request.completed_at = datetime.utcnow()
            if export_file_path:
                request.export_file_path = export_file_path
            if error_message:
                request.error_message = error_message
            
            return True
        except Exception as e:
            logger.error(f"Error updating GDPR request: {e}", exc_info=True, extra={"request_id": request_id})
            return False


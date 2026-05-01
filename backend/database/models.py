"""
Database models for AETHER-SCORE
"""
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

Base = declarative_base()


class User(Base):
    """User model for wallet addresses"""
    __tablename__ = "users"
    
    wallet_address = Column(String(42), primary_key=True)
    email = Column(String(255), nullable=True)
    preferences = Column(JSON, nullable=True)
    gdpr_consent = Column(Boolean, default=False, nullable=False)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    data_deletion_requested = Column(Boolean, default=False, nullable=False)
    deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    scores = relationship("Score", back_populates="user")
    loans = relationship("Loan", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    gdpr_requests = relationship("GDPRRequest", back_populates="user")
    
    __table_args__ = (
        CheckConstraint("wallet_address ~ '^0x[a-fA-F0-9]{40}$'", name="chk_wallet_format"),
        Index('ix_users_wallet_address', 'wallet_address', unique=True),
    )


class Score(Base):
    """Score model for credit scores"""
    __tablename__ = "scores"
    
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), primary_key=True)
    score = Column(Integer, nullable=False)
    risk_band = Column(Integer, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="scores")
    history = relationship("ScoreHistory", back_populates="score_rel")
    
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 1000", name="chk_score_range"),
        CheckConstraint("risk_band >= 0 AND risk_band <= 3", name="chk_risk_band"),
    )


class ScoreHistory(Base):
    """Score history model for tracking score changes"""
    __tablename__ = "score_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("scores.wallet_address"), nullable=False)
    score = Column(Integer, nullable=False)
    risk_band = Column(Integer, nullable=False)
    previous_score = Column(Integer, nullable=True)  # Previous score before this change
    explanation = Column(Text, nullable=True)  # Human-readable explanation of score change
    change_reason = Column(String(50), nullable=True)  # Reason for change: "loan_repayment", "staking_boost", "oracle_penalty", etc.
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    score_rel = relationship("Score", back_populates="history")
    
    __table_args__ = (
        Index('idx_score_history_wallet', 'wallet_address'),
        Index('idx_score_history_computed', 'computed_at'),
        Index('idx_score_history_wallet_computed', 'wallet_address', 'computed_at'),  # Composite index for efficient queries
    )


class UserData(Base):
    """User data model for storing additional user information"""
    __tablename__ = "user_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False)
    data_key = Column(String(100), nullable=False)
    data_value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_user_data_wallet', 'wallet_address'),
        Index('idx_user_data_key', 'data_key'),
    )


class BatchUpdate(Base):
    """Batch update model for tracking batch operations"""
    __tablename__ = "batch_updates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(20), nullable=False)  # pending, processing, completed, failed
    total_count = Column(Integer, nullable=False)
    processed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="chk_batch_status"),
        Index('idx_batch_id', 'batch_id'),
    )


class Loan(Base):
    """Loan model for tracking loan records"""
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    loan_id = Column(Integer, nullable=False)  # On-chain loan ID
    amount = Column(Numeric(20, 8), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    term_days = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, index=True)  # pending, active, repaid, defaulted, liquidated
    collateral_amount = Column(Numeric(20, 8), nullable=True)
    collateral_token = Column(String(42), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    repaid_at = Column(DateTime(timezone=True), nullable=True)
    tx_hash = Column(String(66), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="loans")
    payments = relationship("LoanPayment", back_populates="loan")
    
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_loan_amount"),
        CheckConstraint("interest_rate >= 0 AND interest_rate <= 100", name="chk_interest_rate"),
        CheckConstraint("term_days > 0", name="chk_term_days"),
        CheckConstraint("status IN ('pending', 'active', 'repaid', 'defaulted', 'liquidated')", name="chk_loan_status"),
        Index('idx_loans_wallet', 'wallet_address'),
        Index('idx_loans_status', 'status'),
        Index('idx_loans_created', 'created_at'),
    )


class LoanPayment(Base):
    """Loan payment model for tracking payment history"""
    __tablename__ = "loan_payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False, index=True)
    amount = Column(Numeric(20, 8), nullable=False)
    payment_type = Column(String(20), nullable=False)  # principal, interest, both
    tx_hash = Column(String(66), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    loan = relationship("Loan", back_populates="payments")
    
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payment_amount"),
        CheckConstraint("payment_type IN ('principal', 'interest', 'both')", name="chk_payment_type"),
        Index('idx_payments_loan', 'loan_id'),
    )


class Transaction(Base):
    """Transaction model for on-chain transaction records"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    tx_hash = Column(String(66), nullable=False, unique=True, index=True)
    tx_type = Column(String(50), nullable=False, index=True)  # native_send, native_receive, erc20_transfer, contract_call, etc.
    chain_id = Column(Integer, nullable=False, index=True)  # Chain ID (set from network config)
    chain_name = Column(String(50), nullable=True)  # Human-readable chain name (e.g., "QIE Testnet")
    block_number = Column(Integer, nullable=True, index=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    from_address = Column(String(42), nullable=True, index=True)
    to_address = Column(String(42), nullable=True, index=True)
    value = Column(Numeric(20, 8), nullable=True)
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(Integer, nullable=True)
    status = Column(String(20), nullable=True)  # pending, success, failed
    # Enhanced fields for transaction indexing
    input_data = Column(Text, nullable=True)  # Transaction input data (truncated)
    contract_address = Column(String(42), nullable=True, index=True)  # Contract interacted with
    method_id = Column(String(10), nullable=True)  # First 4 bytes of method signature
    token_transfers_count = Column(Integer, default=0)  # Number of token transfers in this tx
    tx_metadata = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    token_transfers = relationship("TokenTransfer", back_populates="transaction")
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'success', 'failed') OR status IS NULL", name="chk_tx_status"),
        Index('idx_transactions_wallet', 'wallet_address'),
        Index('idx_transactions_hash', 'tx_hash', unique=True),
        Index('idx_transactions_type', 'tx_type'),
        Index('idx_transactions_timestamp', 'block_timestamp'),
        Index('idx_transactions_wallet_chain', 'wallet_address', 'chain_id'),  # Multi-chain queries
    )


class TokenTransfer(Base):
    """Token transfer model for ERC-20/ERC-721 transfers"""
    __tablename__ = "token_transfers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(66), ForeignKey("transactions.tx_hash"), nullable=False, index=True)
    chain_id = Column(Integer, nullable=False, index=True)  # Chain ID (set from network config)
    token_address = Column(String(42), nullable=False, index=True)
    token_type = Column(String(20), nullable=False)  # ERC20, ERC721
    from_address = Column(String(42), nullable=True, index=True)
    to_address = Column(String(42), nullable=True, index=True)
    amount = Column(Numeric(36, 0), nullable=True)  # For ERC20 (can be very large)
    token_id = Column(Numeric(36, 0), nullable=True)  # For ERC721
    block_number = Column(Integer, nullable=True, index=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    transaction = relationship("Transaction", back_populates="token_transfers")
    
    __table_args__ = (
        Index('idx_token_transfers_token', 'token_address'),
        Index('idx_token_transfers_from', 'from_address'),
        Index('idx_token_transfers_to', 'to_address'),
        Index('idx_token_transfers_block', 'block_number'),
        Index('idx_token_transfers_chain', 'chain_id'),
    )


class GDPRRequest(Base):
    """GDPR request model for tracking data access/deletion requests"""
    __tablename__ = "gdpr_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    request_type = Column(String(20), nullable=False)  # deletion, export, access
    status = Column(String(20), nullable=False)  # pending, processing, completed, failed
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    export_file_path = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="gdpr_requests")
    
    __table_args__ = (
        CheckConstraint("request_type IN ('deletion', 'export', 'access')", name="chk_gdpr_request_type"),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="chk_gdpr_status"),
        Index('idx_gdpr_wallet', 'wallet_address'),
        Index('idx_gdpr_status', 'status'),
    )


class DataRetentionLog(Base):
    """Data retention log model for tracking data cleanup operations"""
    __tablename__ = "data_retention_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), nullable=False, index=True)
    records_deleted = Column(Integer, nullable=False)
    archived_count = Column(Integer, nullable=False, server_default='0')
    retention_period_days = Column(Integer, nullable=False)
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(String(20), nullable=True)  # success, failed, partial
    
    __table_args__ = (
        CheckConstraint("status IN ('success', 'failed', 'partial') OR status IS NULL", name="chk_retention_status"),
        Index('idx_retention_table', 'table_name'),
        Index('idx_retention_executed', 'executed_at'),
    )


class ABExperiment(Base):
    """A/B testing experiment model"""
    __tablename__ = "ab_experiments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    variant_a_name = Column(String(50), nullable=False)  # e.g., "rule_based"
    variant_b_name = Column(String(50), nullable=False)  # e.g., "ml_model_v1"
    allocation_ratio = Column(Numeric(3, 2), nullable=False, default=0.5)  # 0.5 = 50/50 split
    status = Column(String(20), nullable=False, default="draft")  # draft, active, paused, completed
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    allocations = relationship("ABAllocation", back_populates="experiment")
    metrics = relationship("ABMetric", back_populates="experiment")
    
    __table_args__ = (
        CheckConstraint("allocation_ratio >= 0 AND allocation_ratio <= 1", name="chk_allocation_ratio"),
        CheckConstraint("status IN ('draft', 'active', 'paused', 'completed')", name="chk_experiment_status"),
        Index('idx_experiment_status', 'status'),
    )


class ABAllocation(Base):
    """User allocation to experiment variants"""
    __tablename__ = "ab_allocations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id"), nullable=False, index=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    variant = Column(String(50), nullable=False)  # "A" or "B"
    allocated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    experiment = relationship("ABExperiment", back_populates="allocations")
    
    __table_args__ = (
        UniqueConstraint('experiment_id', 'wallet_address', name='uq_experiment_user'),
        Index('idx_allocation_experiment_user', 'experiment_id', 'wallet_address'),
    )


class ABMetric(Base):
    """Metrics tracked for A/B experiments"""
    __tablename__ = "ab_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("ab_experiments.id"), nullable=False, index=True)
    wallet_address = Column(String(42), nullable=True, index=True)
    variant = Column(String(50), nullable=False)  # "A" or "B"
    metric_name = Column(String(50), nullable=False)  # e.g., "default_rate", "score_distribution"
    metric_value = Column(Numeric(20, 8), nullable=True)
    metric_data = Column(JSON, nullable=True)  # Additional metric data
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    experiment = relationship("ABExperiment", back_populates="metrics")
    
    __table_args__ = (
        Index('idx_metric_experiment_variant', 'experiment_id', 'variant'),
        Index('idx_metric_recorded', 'recorded_at'),
    )


class LoanOffer(Base):
    """Loan offer model for marketplace offers"""
    __tablename__ = "loan_offers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lender_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    borrower_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=True, index=True)
    amount_min = Column(Numeric(20, 8), nullable=False)
    amount_max = Column(Numeric(20, 8), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)  # APR percentage
    term_days_min = Column(Integer, nullable=False)
    term_days_max = Column(Integer, nullable=False)
    collateral_required = Column(Boolean, default=False, nullable=False)
    accepted_collateral_tokens = Column(JSON, nullable=True)  # Array of token addresses
    ltv_ratio = Column(Numeric(5, 2), nullable=True)  # Loan-to-value ratio
    status = Column(String(20), nullable=False, default='active', index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    extra_metadata = Column(JSON, nullable=True)  # Additional terms (renamed from 'metadata' - reserved word)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lender = relationship("User", foreign_keys=[lender_address])
    borrower = relationship("User", foreign_keys=[borrower_address])
    
    __table_args__ = (
        CheckConstraint("amount_min > 0 AND amount_max >= amount_min", name="chk_offer_amount_range"),
        CheckConstraint("interest_rate >= 0 AND interest_rate <= 100", name="chk_offer_interest_rate"),
        CheckConstraint("term_days_min > 0 AND term_days_max >= term_days_min", name="chk_offer_term_range"),
        CheckConstraint("status IN ('active', 'filled', 'cancelled', 'expired')", name="chk_offer_status"),
        Index('idx_loan_offers_lender', 'lender_address'),
        Index('idx_loan_offers_status', 'status'),
        Index('idx_loan_offers_expires', 'expires_at'),
    )


class LoanRequest(Base):
    """Loan request model for marketplace requests"""
    __tablename__ = "loan_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    borrower_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    amount = Column(Numeric(20, 8), nullable=False)
    max_interest_rate = Column(Numeric(5, 2), nullable=False)  # Maximum acceptable APR
    term_days = Column(Integer, nullable=False)
    collateral_amount = Column(Numeric(20, 8), nullable=True)
    collateral_tokens = Column(JSON, nullable=True)  # Array of available collateral tokens
    request_type = Column(String(20), nullable=False, default='standard')  # 'standard' or 'auction'
    auction_end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default='open', index=True)
    winning_offer_id = Column(Integer, ForeignKey("loan_offers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    borrower = relationship("User", foreign_keys=[borrower_address])
    winning_offer = relationship("LoanOffer", foreign_keys=[winning_offer_id])
    
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_request_amount"),
        CheckConstraint("max_interest_rate >= 0 AND max_interest_rate <= 100", name="chk_request_max_rate"),
        CheckConstraint("term_days > 0", name="chk_request_term"),
        CheckConstraint("request_type IN ('standard', 'auction')", name="chk_request_type"),
        CheckConstraint("status IN ('open', 'bidding', 'accepted', 'expired', 'cancelled')", name="chk_request_status"),
        Index('idx_loan_requests_borrower', 'borrower_address'),
        Index('idx_loan_requests_status', 'status'),
        Index('idx_loan_requests_type', 'request_type'),
    )


class CollateralPosition(Base):
    """Collateral position model for multi-asset collateral"""
    __tablename__ = "collateral_positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False, index=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    token_address = Column(String(42), nullable=False, index=True)
    amount = Column(Numeric(36, 0), nullable=False)  # Token amount (can be very large)
    value_usd = Column(Numeric(20, 8), nullable=False)  # USD value
    ltv_ratio = Column(Numeric(5, 2), nullable=True)  # Current LTV for this position
    health_ratio = Column(Numeric(5, 4), nullable=True)  # Health ratio (0-1)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata (renamed from 'metadata' - reserved word)
    
    # Relationships
    loan = relationship("Loan")
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_collateral_amount"),
        CheckConstraint("value_usd >= 0", name="chk_collateral_value"),
        CheckConstraint("health_ratio >= 0 AND health_ratio <= 1", name="chk_health_ratio"),
        Index('idx_collateral_loan', 'loan_id'),
        Index('idx_collateral_wallet', 'wallet_address'),
        Index('idx_collateral_token', 'token_address'),
    )


class RebalanceHistory(Base):
    """Rebalance history model for tracking collateral rebalancing"""
    __tablename__ = "rebalance_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False, index=True)
    rebalance_type = Column(String(20), nullable=False)  # 'auto' or 'manual'
    from_token = Column(String(42), nullable=False)
    to_token = Column(String(42), nullable=False)
    from_amount = Column(Numeric(36, 0), nullable=False)
    to_amount = Column(Numeric(36, 0), nullable=False)
    tx_hash = Column(String(66), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    loan = relationship("Loan")
    
    __table_args__ = (
        CheckConstraint("rebalance_type IN ('auto', 'manual')", name="chk_rebalance_type"),
        Index('idx_rebalance_loan', 'loan_id'),
        Index('idx_rebalance_created', 'created_at'),
    )


class YieldStrategy(Base):
    """Yield strategy model for yield optimization"""
    __tablename__ = "yield_strategies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    strategy_type = Column(String(20), nullable=False)  # 'staking', 'yield_farming', 'auto_compound'
    protocol = Column(String(100), nullable=False)
    token_address = Column(String(42), nullable=False, index=True)
    amount = Column(Numeric(36, 0), nullable=False)
    apy = Column(Numeric(5, 2), nullable=True)  # Current APY percentage
    auto_compound_enabled = Column(Boolean, default=False, nullable=False)
    last_compounded_at = Column(DateTime(timezone=True), nullable=True)
    total_rewards = Column(Numeric(36, 0), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("strategy_type IN ('staking', 'yield_farming', 'auto_compound')", name="chk_strategy_type"),
        CheckConstraint("amount > 0", name="chk_strategy_amount"),
        CheckConstraint("apy >= 0 AND apy <= 1000", name="chk_strategy_apy"),  # Allow high APY
        Index('idx_yield_wallet', 'wallet_address'),
        Index('idx_yield_type', 'strategy_type'),
        Index('idx_yield_protocol', 'protocol'),
    )


class UserPreferences(Base):
    """User preferences model for loan negotiation and auto-acceptance"""
    __tablename__ = "user_preferences"
    
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), primary_key=True)
    max_interest_rate = Column(Numeric(5, 2), nullable=True)  # Maximum acceptable APR
    term_days_min = Column(Integer, nullable=True)
    term_days_max = Column(Integer, nullable=True)
    max_loan_amount = Column(Numeric(20, 8), nullable=True)
    preferred_collateral_tokens = Column(JSON, nullable=True)  # Array of preferred token addresses
    auto_negotiate_enabled = Column(Boolean, default=False, nullable=False)
    auto_accept_threshold = Column(JSON, nullable=True)  # Conditions for auto-acceptance
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("max_interest_rate IS NULL OR (max_interest_rate >= 0 AND max_interest_rate <= 100)", name="chk_max_interest_rate"),
        CheckConstraint("term_days_min IS NULL OR term_days_min > 0", name="chk_term_days_min"),
        CheckConstraint("term_days_max IS NULL OR term_days_max >= term_days_min", name="chk_term_days_range"),
        CheckConstraint("max_loan_amount IS NULL OR max_loan_amount > 0", name="chk_max_loan_amount"),
    )


class NegotiationSession(Base):
    """Negotiation session model for auto-negotiation tracking"""
    __tablename__ = "negotiation_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    loan_request_id = Column(Integer, ForeignKey("loan_requests.id"), nullable=True)
    preferences_id = Column(String(42), ForeignKey("user_preferences.wallet_address"), nullable=True)
    status = Column(String(20), nullable=False, default='active', index=True)
    current_offer_id = Column(Integer, ForeignKey("loan_offers.id"), nullable=True)
    negotiation_history = Column(JSON, nullable=True)  # Track offers, counters, and actions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    loan_request = relationship("LoanRequest")
    preferences = relationship("UserPreferences", foreign_keys=[preferences_id])
    current_offer = relationship("LoanOffer", foreign_keys=[current_offer_id])
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'completed', 'cancelled', 'expired')", name="chk_negotiation_status"),
        Index('idx_negotiation_wallet', 'wallet_address'),
        Index('idx_negotiation_status', 'status'),
    )


class Alert(Base):
    """Alert model for risk alerts and notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # 'score_drop', 'loan_risk', etc.
    severity = Column(String(20), nullable=False, default='warning')  # 'info', 'warning', 'critical'
    message = Column(Text, nullable=False)
    suggested_actions = Column(JSON, nullable=True)  # Array of suggested actions
    read = Column(Boolean, default=False, nullable=False, index=True)
    dismissed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("severity IN ('info', 'warning', 'critical')", name="chk_alert_severity"),
        Index('idx_alerts_wallet_read', 'wallet_address', 'read'),
        Index('idx_alerts_type_severity', 'alert_type', 'severity'),
    )


class NotificationPreference(Base):
    """Notification preferences model for multi-channel notifications"""
    __tablename__ = "notification_preferences"
    
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), primary_key=True)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=False, nullable=False)
    push_enabled = Column(Boolean, default=False, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    email_address = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("email_address IS NULL OR email_address ~ '^[^@]+@[^@]+\\.[^@]+$'", name="chk_email_format"),
    )


class ScoreShare(Base):
    """Score share model for tracking social media shares"""
    __tablename__ = "score_shares"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    share_type = Column(String(20), nullable=False, index=True)  # 'twitter', 'linkedin', 'facebook', 'custom'
    badge_style = Column(String(20), nullable=False, default='minimal')
    shared_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    share_url = Column(String(500), nullable=True)
    clicks = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("share_type IN ('twitter', 'linkedin', 'facebook', 'custom')", name="chk_share_type"),
        CheckConstraint("badge_style IN ('minimal', 'detailed', 'verified')", name="chk_badge_style"),
        Index('idx_score_shares_wallet', 'wallet_address'),
        Index('idx_score_shares_type', 'share_type'),
        Index('idx_score_shares_shared_at', 'shared_at'),
    )


class LeaderboardEntry(Base):
    """Leaderboard entry model for ranking users"""
    __tablename__ = "leaderboard_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    score = Column(Integer, nullable=False, index=True)
    risk_band = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False, index=True)
    category = Column(String(20), nullable=False, index=True)  # 'all_time', 'monthly', 'weekly'
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 1000", name="chk_leaderboard_score_range"),
        CheckConstraint("risk_band >= 0 AND risk_band <= 3", name="chk_leaderboard_risk_band"),
        CheckConstraint("rank > 0", name="chk_leaderboard_rank"),
        CheckConstraint("category IN ('all_time', 'monthly', 'weekly')", name="chk_leaderboard_category"),
        Index('idx_leaderboard_wallet_category', 'wallet_address', 'category'),
        Index('idx_leaderboard_category_rank', 'category', 'rank'),
        Index('idx_leaderboard_score', 'score'),
    )


class ReferralReward(Base):
    """Referral reward model for tracking NCRD token rewards"""
    __tablename__ = "referral_rewards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"), nullable=True, index=True)
    recipient_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    reward_type = Column(String(20), nullable=False, index=True)  # 'referrer', 'referred', 'milestone'
    amount_ncrd = Column(Numeric(20, 8), nullable=False)
    status = Column(String(20), nullable=False, default='pending', index=True)  # 'pending', 'distributed', 'failed'
    distribution_tx_hash = Column(String(66), nullable=True, index=True)
    distributed_at = Column(DateTime(timezone=True), nullable=True)
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata (renamed from 'metadata' - reserved word)  # Additional reward metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_address])
    
    __table_args__ = (
        CheckConstraint("reward_type IN ('referrer', 'referred', 'milestone')", name="chk_reward_type"),
        CheckConstraint("status IN ('pending', 'distributed', 'failed')", name="chk_reward_status"),
        CheckConstraint("amount_ncrd > 0", name="chk_reward_amount"),
        Index('idx_referral_rewards_recipient_status', 'recipient_address', 'status'),
        Index('idx_referral_rewards_status', 'status'),
    )


class Team(Base):
    """Team model for DAOs/organizations"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String(100), nullable=False, index=True)
    team_type = Column(String(20), nullable=False, default='custom')  # 'dao', 'organization', 'custom'
    admin_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_address])
    members = relationship("TeamMember", back_populates="team")
    scores = relationship("TeamScore", back_populates="team")
    
    __table_args__ = (
        CheckConstraint("team_type IN ('dao', 'organization', 'custom')", name="chk_team_type"),
        Index('idx_teams_admin', 'admin_address'),
    )


class TeamMember(Base):
    """Team member model"""
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default='member')  # 'admin', 'member'
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    contribution_score = Column(Numeric(5, 2), nullable=True)  # For weighted calculations
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", foreign_keys=[wallet_address])
    
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'member')", name="chk_team_member_role"),
        UniqueConstraint('team_id', 'wallet_address', name='uq_team_member'),
        Index('idx_team_members_team', 'team_id'),
        Index('idx_team_members_wallet', 'wallet_address'),
    )


class TeamScore(Base):
    """Team score model for aggregate team credit scores"""
    __tablename__ = "team_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    aggregate_score = Column(Integer, nullable=False)
    member_count = Column(Integer, nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    team = relationship("Team", back_populates="scores")
    
    __table_args__ = (
        CheckConstraint("aggregate_score >= 0 AND aggregate_score <= 1000", name="chk_team_score_range"),
        CheckConstraint("member_count > 0", name="chk_team_member_count"),
        Index('idx_team_scores_team', 'team_id'),
        Index('idx_team_scores_calculated', 'calculated_at'),
    )


class CreditReport(Base):
    """Credit report model for storing generated reports"""
    __tablename__ = "credit_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    report_type = Column(String(20), nullable=False, default='full')  # 'full', 'summary', 'custom'
    format = Column(String(10), nullable=False, default='pdf')  # 'pdf', 'json', 'csv'
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata (renamed from 'metadata' - reserved word)  # Report metadata and data
    
    # Relationships
    user = relationship("User")
    shares = relationship("ReportShare", back_populates="report")
    
    __table_args__ = (
        CheckConstraint("report_type IN ('full', 'summary', 'custom')", name="chk_report_type"),
        CheckConstraint("format IN ('pdf', 'json', 'csv')", name="chk_report_format"),
        Index('idx_credit_reports_wallet', 'wallet_address'),
        Index('idx_credit_reports_generated', 'generated_at'),
    )


class ReportShare(Base):
    """Report share model for sharing reports with protocols"""
    __tablename__ = "report_shares"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("credit_reports.id"), nullable=False, index=True)
    wallet_address = Column(String(42), ForeignKey("users.wallet_address"), nullable=False, index=True)
    shared_with_address = Column(String(42), nullable=False, index=True)  # Protocol or user address
    share_token = Column(String(100), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    accessed_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    report = relationship("CreditReport", back_populates="shares")
    user = relationship("User", foreign_keys=[wallet_address])
    
    __table_args__ = (
        Index('idx_report_shares_token', 'share_token', unique=True),
        Index('idx_report_shares_wallet', 'wallet_address'),
        Index('idx_report_shares_shared_with', 'shared_with_address'),
        Index('idx_report_shares_expires', 'expires_at'),
    )


class APIAccess(Base):
    """API access model for third-party protocol access"""
    __tablename__ = "api_access"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_address = Column(String(42), nullable=False, index=True)
    api_key = Column(String(100), nullable=False, unique=True, index=True)  # Hashed API key
    permissions = Column(JSON, nullable=True)  # Scoped permissions
    rate_limit = Column(Integer, default=60, nullable=False)  # Requests per minute
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        CheckConstraint("rate_limit > 0", name="chk_rate_limit"),
        Index('idx_api_access_protocol', 'protocol_address'),
        Index('idx_api_access_key', 'api_key', unique=True),
        Index('idx_api_access_expires', 'expires_at'),
    )


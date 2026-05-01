"""defi_integration_features

Revision ID: 005_defi_integration_features
Revises: 004_advanced_scoring_features
Create Date: 2025-12-18 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_defi_integration_features'
down_revision = '004_advanced_scoring_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create loan_offers table
    op.create_table(
        'loan_offers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lender_address', sa.String(length=42), nullable=False),
        sa.Column('borrower_address', sa.String(length=42), nullable=True),
        sa.Column('amount_min', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('amount_max', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('term_days_min', sa.Integer(), nullable=False),
        sa.Column('term_days_max', sa.Integer(), nullable=False),
        sa.Column('collateral_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('accepted_collateral_tokens', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ltv_ratio', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lender_address'], ['users.wallet_address'], ),
        sa.ForeignKeyConstraint(['borrower_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount_min > 0 AND amount_max >= amount_min', name='chk_offer_amount_range'),
        sa.CheckConstraint('interest_rate >= 0 AND interest_rate <= 100', name='chk_offer_interest_rate'),
        sa.CheckConstraint('term_days_min > 0 AND term_days_max >= term_days_min', name='chk_offer_term_range'),
        sa.CheckConstraint("status IN ('active', 'filled', 'cancelled', 'expired')", name='chk_offer_status')
    )
    op.create_index('idx_loan_offers_lender', 'loan_offers', ['lender_address'], unique=False)
    op.create_index('idx_loan_offers_status', 'loan_offers', ['status'], unique=False)
    op.create_index('idx_loan_offers_expires', 'loan_offers', ['expires_at'], unique=False)
    
    # Create loan_requests table
    op.create_table(
        'loan_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('borrower_address', sa.String(length=42), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('max_interest_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('term_days', sa.Integer(), nullable=False),
        sa.Column('collateral_amount', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('collateral_tokens', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('request_type', sa.String(length=20), nullable=False, server_default='standard'),
        sa.Column('auction_end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('winning_offer_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['borrower_address'], ['users.wallet_address'], ),
        sa.ForeignKeyConstraint(['winning_offer_id'], ['loan_offers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='chk_request_amount'),
        sa.CheckConstraint('max_interest_rate >= 0 AND max_interest_rate <= 100', name='chk_request_max_rate'),
        sa.CheckConstraint('term_days > 0', name='chk_request_term'),
        sa.CheckConstraint("request_type IN ('standard', 'auction')", name='chk_request_type'),
        sa.CheckConstraint("status IN ('open', 'bidding', 'accepted', 'expired', 'cancelled')", name='chk_request_status')
    )
    op.create_index('idx_loan_requests_borrower', 'loan_requests', ['borrower_address'], unique=False)
    op.create_index('idx_loan_requests_status', 'loan_requests', ['status'], unique=False)
    op.create_index('idx_loan_requests_type', 'loan_requests', ['request_type'], unique=False)
    
    # Create collateral_positions table
    op.create_table(
        'collateral_positions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('token_address', sa.String(length=42), nullable=False),
        sa.Column('amount', sa.Numeric(precision=36, scale=0), nullable=False),
        sa.Column('value_usd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('ltv_ratio', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('health_ratio', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='chk_collateral_amount'),
        sa.CheckConstraint('value_usd >= 0', name='chk_collateral_value'),
        sa.CheckConstraint('health_ratio >= 0 AND health_ratio <= 1', name='chk_health_ratio')
    )
    op.create_index('idx_collateral_loan', 'collateral_positions', ['loan_id'], unique=False)
    op.create_index('idx_collateral_wallet', 'collateral_positions', ['wallet_address'], unique=False)
    op.create_index('idx_collateral_token', 'collateral_positions', ['token_address'], unique=False)
    
    # Create rebalance_history table
    op.create_table(
        'rebalance_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('rebalance_type', sa.String(length=20), nullable=False),
        sa.Column('from_token', sa.String(length=42), nullable=False),
        sa.Column('to_token', sa.String(length=42), nullable=False),
        sa.Column('from_amount', sa.Numeric(precision=36, scale=0), nullable=False),
        sa.Column('to_amount', sa.Numeric(precision=36, scale=0), nullable=False),
        sa.Column('tx_hash', sa.String(length=66), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("rebalance_type IN ('auto', 'manual')", name='chk_rebalance_type')
    )
    op.create_index('idx_rebalance_loan', 'rebalance_history', ['loan_id'], unique=False)
    op.create_index('idx_rebalance_created', 'rebalance_history', ['created_at'], unique=False)
    
    # Create yield_strategies table
    op.create_table(
        'yield_strategies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('strategy_type', sa.String(length=20), nullable=False),
        sa.Column('protocol', sa.String(length=100), nullable=False),
        sa.Column('token_address', sa.String(length=42), nullable=False),
        sa.Column('amount', sa.Numeric(precision=36, scale=0), nullable=False),
        sa.Column('apy', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('auto_compound_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_compounded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_rewards', sa.Numeric(precision=36, scale=0), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("strategy_type IN ('staking', 'yield_farming', 'auto_compound')", name='chk_strategy_type'),
        sa.CheckConstraint('amount > 0', name='chk_strategy_amount'),
        sa.CheckConstraint('apy >= 0 AND apy <= 1000', name='chk_strategy_apy')
    )
    op.create_index('idx_yield_wallet', 'yield_strategies', ['wallet_address'], unique=False)
    op.create_index('idx_yield_type', 'yield_strategies', ['strategy_type'], unique=False)
    op.create_index('idx_yield_protocol', 'yield_strategies', ['protocol'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_yield_protocol', table_name='yield_strategies')
    op.drop_index('idx_yield_type', table_name='yield_strategies')
    op.drop_index('idx_yield_wallet', table_name='yield_strategies')
    op.drop_table('yield_strategies')
    
    op.drop_index('idx_rebalance_created', table_name='rebalance_history')
    op.drop_index('idx_rebalance_loan', table_name='rebalance_history')
    op.drop_table('rebalance_history')
    
    op.drop_index('idx_collateral_token', table_name='collateral_positions')
    op.drop_index('idx_collateral_wallet', table_name='collateral_positions')
    op.drop_index('idx_collateral_loan', table_name='collateral_positions')
    op.drop_table('collateral_positions')
    
    op.drop_index('idx_loan_requests_type', table_name='loan_requests')
    op.drop_index('idx_loan_requests_status', table_name='loan_requests')
    op.drop_index('idx_loan_requests_borrower', table_name='loan_requests')
    op.drop_table('loan_requests')
    
    op.drop_index('idx_loan_offers_expires', table_name='loan_offers')
    op.drop_index('idx_loan_offers_status', table_name='loan_offers')
    op.drop_index('idx_loan_offers_lender', table_name='loan_offers')
    op.drop_table('loan_offers')


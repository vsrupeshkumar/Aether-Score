"""advanced_scoring_features

Revision ID: 004_advanced_scoring_features
Revises: 003_add_score_history_fields
Create Date: 2025-12-18 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_advanced_scoring_features'
down_revision = '003_add_score_history_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add chain support to transactions
    op.add_column('transactions', sa.Column('chain_id', sa.Integer(), nullable=False, server_default='1983'))
    op.add_column('transactions', sa.Column('chain_name', sa.String(length=50), nullable=True))
    op.create_index('idx_transactions_wallet_chain', 'transactions', ['wallet_address', 'chain_id'], unique=False)
    
    # Add chain support to token_transfers
    op.add_column('token_transfers', sa.Column('chain_id', sa.Integer(), nullable=False, server_default='1983'))
    op.create_index('idx_token_transfers_chain', 'token_transfers', ['chain_id'], unique=False)
    
    # Create unified_identity table
    op.create_table(
        'unified_identity',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('primary_address', sa.String(length=42), nullable=False),
        sa.Column('chain_id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=42), nullable=False),
        sa.Column('linked_via', sa.String(length=20), nullable=False, server_default='same_address'),
        sa.Column('bridge_tx_hash', sa.String(length=66), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('address', 'chain_id', name='uq_address_chain')
    )
    op.create_index('idx_unified_identity_primary', 'unified_identity', ['primary_address'], unique=False)
    op.create_index('idx_unified_identity_address', 'unified_identity', ['address', 'chain_id'], unique=False)
    
    # Create chain_scores table
    op.create_table(
        'chain_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('unified_identity_id', sa.Integer(), nullable=True),
        sa.Column('chain_id', sa.Integer(), nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('risk_band', sa.Integer(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['unified_identity_id'], ['unified_identity.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('score >= 0 AND score <= 1000', name='chk_chain_score_range'),
        sa.CheckConstraint('risk_band >= 0 AND risk_band <= 3', name='chk_chain_risk_band')
    )
    op.create_index('idx_chain_scores_identity', 'chain_scores', ['unified_identity_id', 'chain_id'], unique=False)
    op.create_index('idx_chain_scores_address', 'chain_scores', ['wallet_address', 'chain_id'], unique=False)
    
    # Create governance_activity table
    op.create_table(
        'governance_activity',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('chain_id', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(length=100), nullable=False),
        sa.Column('activity_type', sa.String(length=20), nullable=False),
        sa.Column('proposal_id', sa.String(length=100), nullable=True),
        sa.Column('tx_hash', sa.String(length=66), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("activity_type IN ('vote', 'proposal', 'delegation', 'delegate')", name='chk_governance_type')
    )
    op.create_index('idx_governance_wallet', 'governance_activity', ['wallet_address'], unique=False)
    op.create_index('idx_governance_protocol', 'governance_activity', ['protocol'], unique=False)
    op.create_index('idx_governance_type', 'governance_activity', ['activity_type'], unique=False)
    op.create_index('idx_governance_timestamp', 'governance_activity', ['timestamp'], unique=False)
    
    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('referrer_address', sa.String(length=42), nullable=False),
        sa.Column('referred_address', sa.String(length=42), nullable=True),
        sa.Column('referral_code', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('score_boost_applied', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['referrer_address'], ['users.wallet_address'], ),
        sa.ForeignKeyConstraint(['referred_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('referral_code'),
        sa.CheckConstraint("status IN ('pending', 'active', 'completed')", name='chk_referral_status')
    )
    op.create_index('idx_referrals_referrer', 'referrals', ['referrer_address'], unique=False)
    op.create_index('idx_referrals_referred', 'referrals', ['referred_address'], unique=False)
    op.create_index('idx_referrals_code', 'referrals', ['referral_code'], unique=True)
    
    # Create verification_badges table
    op.create_table(
        'verification_badges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('badge_type', sa.String(length=50), nullable=False),
        sa.Column('issuer', sa.String(length=100), nullable=False),
        sa.Column('score_boost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("badge_type IN ('community_verified', 'governance_participant', 'early_adopter', 'liquidity_provider', 'defi_expert', 'nft_collector', 'gaming_enthusiast')", name='chk_badge_type'),
        sa.CheckConstraint('score_boost >= 0 AND score_boost <= 100', name='chk_badge_boost_range')
    )
    op.create_index('idx_badges_wallet', 'verification_badges', ['wallet_address'], unique=False)
    op.create_index('idx_badges_type', 'verification_badges', ['badge_type'], unique=False)
    op.create_index('idx_badges_expires', 'verification_badges', ['expires_at'], unique=False)
    
    # Create industry_profiles table
    op.create_table(
        'industry_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('industry_category', sa.String(length=20), nullable=False),
        sa.Column('activity_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dominant_category', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('category_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_analyzed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("industry_category IN ('defi', 'nft', 'gaming', 'dao', 'bridge', 'dex', 'lending', 'mixed')", name='chk_industry_category'),
        sa.CheckConstraint('activity_score >= 0 AND activity_score <= 100', name='chk_activity_score_range'),
        sa.UniqueConstraint('wallet_address')
    )
    op.create_index('idx_industry_wallet', 'industry_profiles', ['wallet_address'], unique=True)
    op.create_index('idx_industry_category', 'industry_profiles', ['industry_category'], unique=False)


def downgrade() -> None:
    # Drop new tables
    op.drop_index('idx_industry_category', table_name='industry_profiles')
    op.drop_index('idx_industry_wallet', table_name='industry_profiles')
    op.drop_table('industry_profiles')
    
    op.drop_index('idx_badges_expires', table_name='verification_badges')
    op.drop_index('idx_badges_type', table_name='verification_badges')
    op.drop_index('idx_badges_wallet', table_name='verification_badges')
    op.drop_table('verification_badges')
    
    op.drop_index('idx_referrals_code', table_name='referrals')
    op.drop_index('idx_referrals_referred', table_name='referrals')
    op.drop_index('idx_referrals_referrer', table_name='referrals')
    op.drop_table('referrals')
    
    op.drop_index('idx_governance_timestamp', table_name='governance_activity')
    op.drop_index('idx_governance_type', table_name='governance_activity')
    op.drop_index('idx_governance_protocol', table_name='governance_activity')
    op.drop_index('idx_governance_wallet', table_name='governance_activity')
    op.drop_table('governance_activity')
    
    op.drop_index('idx_chain_scores_address', table_name='chain_scores')
    op.drop_index('idx_chain_scores_identity', table_name='chain_scores')
    op.drop_table('chain_scores')
    
    op.drop_index('idx_unified_identity_address', table_name='unified_identity')
    op.drop_index('idx_unified_identity_primary', table_name='unified_identity')
    op.drop_table('unified_identity')
    
    # Remove chain support from token_transfers
    op.drop_index('idx_token_transfers_chain', table_name='token_transfers')
    op.drop_column('token_transfers', 'chain_id')
    
    # Remove chain support from transactions
    op.drop_index('idx_transactions_wallet_chain', table_name='transactions')
    op.drop_column('transactions', 'chain_name')
    op.drop_column('transactions', 'chain_id')


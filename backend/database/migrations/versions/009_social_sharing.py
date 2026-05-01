"""social_sharing

Revision ID: 009_social_sharing
Revises: 008_risk_alerts
Create Date: 2025-12-18 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_social_sharing'
down_revision = '008_risk_alerts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create score_shares table
    op.create_table(
        'score_shares',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('share_type', sa.String(length=20), nullable=False),
        sa.Column('badge_style', sa.String(length=20), nullable=False, server_default='minimal'),
        sa.Column('shared_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('share_url', sa.String(length=500), nullable=True),
        sa.Column('clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("share_type IN ('twitter', 'linkedin', 'facebook', 'custom')", name='chk_share_type'),
        sa.CheckConstraint("badge_style IN ('minimal', 'detailed', 'verified')", name='chk_badge_style')
    )
    op.create_index('idx_score_shares_wallet', 'score_shares', ['wallet_address'], unique=False)
    op.create_index('idx_score_shares_type', 'score_shares', ['share_type'], unique=False)
    op.create_index('idx_score_shares_shared_at', 'score_shares', ['shared_at'], unique=False)
    
    # Create leaderboard_entries table
    op.create_table(
        'leaderboard_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('risk_band', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('score >= 0 AND score <= 1000', name='chk_leaderboard_score_range'),
        sa.CheckConstraint('risk_band >= 0 AND risk_band <= 3', name='chk_leaderboard_risk_band'),
        sa.CheckConstraint('rank > 0', name='chk_leaderboard_rank'),
        sa.CheckConstraint("category IN ('all_time', 'monthly', 'weekly')", name='chk_leaderboard_category')
    )
    op.create_index('idx_leaderboard_wallet_category', 'leaderboard_entries', ['wallet_address', 'category'], unique=False)
    op.create_index('idx_leaderboard_category_rank', 'leaderboard_entries', ['category', 'rank'], unique=False)
    op.create_index('idx_leaderboard_score', 'leaderboard_entries', ['score'], unique=False)
    op.create_index('idx_leaderboard_wallet_address', 'leaderboard_entries', ['wallet_address'], unique=False)
    op.create_index('idx_leaderboard_category', 'leaderboard_entries', ['category'], unique=False)
    op.create_index('idx_leaderboard_rank', 'leaderboard_entries', ['rank'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_leaderboard_rank', table_name='leaderboard_entries')
    op.drop_index('idx_leaderboard_category', table_name='leaderboard_entries')
    op.drop_index('idx_leaderboard_wallet_address', table_name='leaderboard_entries')
    op.drop_index('idx_leaderboard_score', table_name='leaderboard_entries')
    op.drop_index('idx_leaderboard_category_rank', table_name='leaderboard_entries')
    op.drop_index('idx_leaderboard_wallet_category', table_name='leaderboard_entries')
    op.drop_table('leaderboard_entries')
    op.drop_index('idx_score_shares_shared_at', table_name='score_shares')
    op.drop_index('idx_score_shares_type', table_name='score_shares')
    op.drop_index('idx_score_shares_wallet', table_name='score_shares')
    op.drop_table('score_shares')


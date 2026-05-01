"""referral_rewards

Revision ID: 010_referral_rewards
Revises: 009_social_sharing
Create Date: 2025-12-18 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_referral_rewards'
down_revision = '009_social_sharing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create referral_rewards table
    op.create_table(
        'referral_rewards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('referral_id', sa.Integer(), nullable=True),
        sa.Column('recipient_address', sa.String(length=42), nullable=False),
        sa.Column('reward_type', sa.String(length=20), nullable=False),
        sa.Column('amount_ncrd', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('distribution_tx_hash', sa.String(length=66), nullable=True),
        sa.Column('distributed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['referral_id'], ['referrals.id'], ),
        sa.ForeignKeyConstraint(['recipient_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("reward_type IN ('referrer', 'referred', 'milestone')", name='chk_reward_type'),
        sa.CheckConstraint("status IN ('pending', 'distributed', 'failed')", name='chk_reward_status'),
        sa.CheckConstraint('amount_ncrd > 0', name='chk_reward_amount')
    )
    op.create_index('idx_referral_rewards_recipient_status', 'referral_rewards', ['recipient_address', 'status'], unique=False)
    op.create_index('idx_referral_rewards_status', 'referral_rewards', ['status'], unique=False)
    op.create_index('idx_referral_rewards_referral_id', 'referral_rewards', ['referral_id'], unique=False)
    op.create_index('idx_referral_rewards_recipient_address', 'referral_rewards', ['recipient_address'], unique=False)
    
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('team_name', sa.String(length=100), nullable=False),
        sa.Column('team_type', sa.String(length=20), nullable=False, server_default='custom'),
        sa.Column('admin_address', sa.String(length=42), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['admin_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("team_type IN ('dao', 'organization', 'custom')", name='chk_team_type')
    )
    op.create_index('idx_teams_admin', 'teams', ['admin_address'], unique=False)
    op.create_index('idx_teams_team_name', 'teams', ['team_name'], unique=False)
    
    # Create team_members table
    op.create_table(
        'team_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('contribution_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("role IN ('admin', 'member')", name='chk_team_member_role'),
        sa.UniqueConstraint('team_id', 'wallet_address', name='uq_team_member')
    )
    op.create_index('idx_team_members_team', 'team_members', ['team_id'], unique=False)
    op.create_index('idx_team_members_wallet', 'team_members', ['wallet_address'], unique=False)
    
    # Create team_scores table
    op.create_table(
        'team_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('aggregate_score', sa.Integer(), nullable=False),
        sa.Column('member_count', sa.Integer(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('aggregate_score >= 0 AND aggregate_score <= 1000', name='chk_team_score_range'),
        sa.CheckConstraint('member_count > 0', name='chk_team_member_count')
    )
    op.create_index('idx_team_scores_team', 'team_scores', ['team_id'], unique=False)
    op.create_index('idx_team_scores_calculated', 'team_scores', ['calculated_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_team_scores_calculated', table_name='team_scores')
    op.drop_index('idx_team_scores_team', table_name='team_scores')
    op.drop_table('team_scores')
    op.drop_index('idx_team_members_wallet', table_name='team_members')
    op.drop_index('idx_team_members_team', table_name='team_members')
    op.drop_table('team_members')
    op.drop_index('idx_teams_team_name', table_name='teams')
    op.drop_index('idx_teams_admin', table_name='teams')
    op.drop_table('teams')
    op.drop_index('idx_referral_rewards_recipient_address', table_name='referral_rewards')
    op.drop_index('idx_referral_rewards_referral_id', table_name='referral_rewards')
    op.drop_index('idx_referral_rewards_status', table_name='referral_rewards')
    op.drop_index('idx_referral_rewards_recipient_status', table_name='referral_rewards')
    op.drop_table('referral_rewards')


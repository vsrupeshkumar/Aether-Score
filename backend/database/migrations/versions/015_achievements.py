"""achievements

Revision ID: 015_achievements
Revises: 014_mobile_notifications
Create Date: 2025-12-18 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015_achievements'
down_revision = '014_mobile_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create achievements table
    op.create_table(
        'achievements',
        sa.Column('achievement_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('icon', sa.String(length=10), nullable=True),
        sa.Column('category', sa.String(length=20), nullable=False, server_default='general'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('achievement_id'),
        sa.CheckConstraint("category IN ('score', 'loan', 'staking', 'transaction', 'milestone', 'general')", name='chk_achievement_category')
    )
    op.create_index('idx_achievements_category', 'achievements', ['category'], unique=False)
    
    # Create user_achievements table
    op.create_table(
        'user_achievements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('achievement_id', sa.String(length=50), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.achievement_id'], ),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('wallet_address', 'achievement_id', name='uq_user_achievement')
    )
    op.create_index('idx_user_achievements_wallet', 'user_achievements', ['wallet_address'], unique=False)
    op.create_index('idx_user_achievements_achievement', 'user_achievements', ['achievement_id'], unique=False)
    op.create_index('idx_user_achievements_unlocked', 'user_achievements', ['unlocked_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_user_achievements_unlocked', table_name='user_achievements')
    op.drop_index('idx_user_achievements_achievement', table_name='user_achievements')
    op.drop_index('idx_user_achievements_wallet', table_name='user_achievements')
    op.drop_table('user_achievements')
    op.drop_index('idx_achievements_category', table_name='achievements')
    op.drop_table('achievements')


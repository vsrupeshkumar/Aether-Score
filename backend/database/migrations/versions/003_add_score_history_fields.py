"""add_score_history_fields

Revision ID: 003_add_score_history_fields
Revises: 002_expand_schema
Create Date: 2025-12-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_score_history_fields'
down_revision = '002_expand_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to score_history table
    op.add_column('score_history', sa.Column('previous_score', sa.Integer(), nullable=True))
    op.add_column('score_history', sa.Column('explanation', sa.Text(), nullable=True))
    op.add_column('score_history', sa.Column('change_reason', sa.String(length=50), nullable=True))
    
    # Add composite index for efficient queries
    op.create_index(
        'idx_score_history_wallet_computed',
        'score_history',
        ['wallet_address', 'computed_at'],
        unique=False
    )


def downgrade() -> None:
    # Remove composite index
    op.drop_index('idx_score_history_wallet_computed', table_name='score_history')
    
    # Remove columns
    op.drop_column('score_history', 'change_reason')
    op.drop_column('score_history', 'explanation')
    op.drop_column('score_history', 'previous_score')


"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create scores table
    op.create_table(
        'scores',
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('risk_band', sa.Integer(), nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('wallet_address')
    )
    op.create_index('idx_scores_last_updated', 'scores', ['last_updated'], unique=False)
    op.create_index(op.f('ix_scores_wallet_address'), 'scores', ['wallet_address'], unique=True)
    
    # Create score_history table
    op.create_table(
        'score_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('risk_band', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_history_address', 'score_history', ['wallet_address'], unique=False)
    op.create_index('idx_history_timestamp', 'score_history', ['timestamp'], unique=False)
    op.create_index('idx_history_address_timestamp', 'score_history', ['wallet_address', 'timestamp'], unique=False)
    
    # Create user_data table
    op.create_table(
        'user_data',
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('wallet_address')
    )
    op.create_index('idx_user_data_updated', 'user_data', ['updated_at'], unique=False)
    op.create_index(op.f('ix_user_data_wallet_address'), 'user_data', ['wallet_address'], unique=True)
    
    # Create batch_updates table
    op.create_table(
        'batch_updates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('batch_id', sa.String(length=64), nullable=False),
        sa.Column('addresses', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_id')
    )
    op.create_index('idx_batch_status', 'batch_updates', ['status'], unique=False)
    op.create_index('idx_batch_created', 'batch_updates', ['created_at'], unique=False)
    op.create_index(op.f('ix_batch_updates_batch_id'), 'batch_updates', ['batch_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_batch_updates_batch_id'), table_name='batch_updates')
    op.drop_index('idx_batch_created', table_name='batch_updates')
    op.drop_index('idx_batch_status', table_name='batch_updates')
    op.drop_table('batch_updates')
    
    op.drop_index(op.f('ix_user_data_wallet_address'), table_name='user_data')
    op.drop_index('idx_user_data_updated', table_name='user_data')
    op.drop_table('user_data')
    
    op.drop_index('idx_history_address_timestamp', table_name='score_history')
    op.drop_index('idx_history_timestamp', table_name='score_history')
    op.drop_index('idx_history_address', table_name='score_history')
    op.drop_table('score_history')
    
    op.drop_index(op.f('ix_scores_wallet_address'), table_name='scores')
    op.drop_index('idx_scores_last_updated', table_name='scores')
    op.drop_table('scores')


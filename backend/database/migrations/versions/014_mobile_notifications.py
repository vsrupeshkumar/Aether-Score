"""mobile_notifications

Revision ID: 014_mobile_notifications
Revises: 013_credit_reports
Create Date: 2025-12-18 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014_mobile_notifications'
down_revision = '013_credit_reports'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create device_tokens table
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('device_token', sa.String(length=500), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.Column('app_version', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("platform IN ('ios', 'android', 'web')", name='chk_device_platform'),
        sa.UniqueConstraint('device_token', name='uq_device_tokens_token')
    )
    op.create_index('idx_device_tokens_wallet', 'device_tokens', ['wallet_address'], unique=False)
    op.create_index('idx_device_tokens_token', 'device_tokens', ['device_token'], unique=True)
    op.create_index('idx_device_tokens_platform', 'device_tokens', ['platform'], unique=False)
    
    # Add phone_number to notification_preferences if it doesn't exist
    try:
        op.add_column('notification_preferences', sa.Column('phone_number', sa.String(length=20), nullable=True))
    except:
        # Column might already exist
        pass


def downgrade() -> None:
    op.drop_index('idx_device_tokens_platform', table_name='device_tokens')
    op.drop_index('idx_device_tokens_token', table_name='device_tokens')
    op.drop_index('idx_device_tokens_wallet', table_name='device_tokens')
    op.drop_table('device_tokens')
    
    # Remove phone_number column if it exists
    try:
        op.drop_column('notification_preferences', 'phone_number')
    except:
        pass


"""developer_api

Revision ID: 016_developer_api
Revises: 015_achievements
Create Date: 2025-12-18 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016_developer_api'
down_revision = '015_achievements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key_hash', sa.String(length=100), nullable=False),
        sa.Column('developer_address', sa.String(length=42), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('tier', sa.String(length=20), nullable=False, server_default='free'),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("tier IN ('free', 'paid', 'enterprise')", name='chk_api_key_tier'),
        sa.CheckConstraint('rate_limit_per_minute > 0', name='chk_rate_limit_minute'),
        sa.CheckConstraint('rate_limit_per_day > 0', name='chk_rate_limit_day'),
        sa.UniqueConstraint('key_hash', name='uq_api_keys_hash')
    )
    op.create_index('idx_api_keys_developer', 'api_keys', ['developer_address'], unique=False)
    op.create_index('idx_api_keys_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('idx_api_keys_expires', 'api_keys', ['expires_at'], unique=False)
    
    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('secret', sa.String(length=100), nullable=False),
        sa.Column('events', sa.JSON(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('failure_count >= 0', name='chk_webhook_failure_count')
    )
    op.create_index('idx_webhooks_api_key', 'webhooks', ['api_key_id'], unique=False)
    op.create_index('idx_webhooks_active', 'webhooks', ['active'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_webhooks_active', table_name='webhooks')
    op.drop_index('idx_webhooks_api_key', table_name='webhooks')
    op.drop_table('webhooks')
    op.drop_index('idx_api_keys_expires', table_name='api_keys')
    op.drop_index('idx_api_keys_hash', table_name='api_keys')
    op.drop_index('idx_api_keys_developer', table_name='api_keys')
    op.drop_table('api_keys')


"""credit_reports

Revision ID: 013_credit_reports
Revises: 010_referral_rewards
Create Date: 2025-12-18 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013_credit_reports'
down_revision = '010_referral_rewards'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create credit_reports table
    op.create_table(
        'credit_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('report_type', sa.String(length=20), nullable=False, server_default='full'),
        sa.Column('format', sa.String(length=10), nullable=False, server_default='pdf'),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("report_type IN ('full', 'summary', 'custom')", name='chk_report_type'),
        sa.CheckConstraint("format IN ('pdf', 'json', 'csv')", name='chk_report_format')
    )
    op.create_index('idx_credit_reports_wallet', 'credit_reports', ['wallet_address'], unique=False)
    op.create_index('idx_credit_reports_generated', 'credit_reports', ['generated_at'], unique=False)
    
    # Create report_shares table
    op.create_table(
        'report_shares',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('shared_with_address', sa.String(length=42), nullable=False),
        sa.Column('share_token', sa.String(length=100), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['credit_reports.id'], ),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_token', name='uq_report_shares_token')
    )
    op.create_index('idx_report_shares_token', 'report_shares', ['share_token'], unique=True)
    op.create_index('idx_report_shares_wallet', 'report_shares', ['wallet_address'], unique=False)
    op.create_index('idx_report_shares_shared_with', 'report_shares', ['shared_with_address'], unique=False)
    op.create_index('idx_report_shares_expires', 'report_shares', ['expires_at'], unique=False)
    op.create_index('idx_report_shares_report_id', 'report_shares', ['report_id'], unique=False)
    
    # Create api_access table
    op.create_table(
        'api_access',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('protocol_address', sa.String(length=42), nullable=False),
        sa.Column('api_key', sa.String(length=100), nullable=False),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('rate_limit > 0', name='chk_rate_limit'),
        sa.UniqueConstraint('api_key', name='uq_api_access_key')
    )
    op.create_index('idx_api_access_protocol', 'api_access', ['protocol_address'], unique=False)
    op.create_index('idx_api_access_key', 'api_access', ['api_key'], unique=True)
    op.create_index('idx_api_access_expires', 'api_access', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_api_access_expires', table_name='api_access')
    op.drop_index('idx_api_access_key', table_name='api_access')
    op.drop_index('idx_api_access_protocol', table_name='api_access')
    op.drop_table('api_access')
    op.drop_index('idx_report_shares_report_id', table_name='report_shares')
    op.drop_index('idx_report_shares_expires', table_name='report_shares')
    op.drop_index('idx_report_shares_shared_with', table_name='report_shares')
    op.drop_index('idx_report_shares_wallet', table_name='report_shares')
    op.drop_index('idx_report_shares_token', table_name='report_shares')
    op.drop_table('report_shares')
    op.drop_index('idx_credit_reports_generated', table_name='credit_reports')
    op.drop_index('idx_credit_reports_wallet', table_name='credit_reports')
    op.drop_table('credit_reports')


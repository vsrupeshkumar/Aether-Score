"""expand_schema

Revision ID: 002_expand_schema
Revises: 001_initial_schema
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_expand_schema'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table (GDPR compliant)
    op.create_table(
        'users',
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('gdpr_consent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('consent_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_deletion_requested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deletion_requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('wallet_address'),
        sa.CheckConstraint("wallet_address ~ '^0x[a-fA-F0-9]{40}$'", name='chk_wallet_format')
    )
    op.create_index(op.f('ix_users_wallet_address'), 'users', ['wallet_address'], unique=True)
    
    # Create loans table
    op.create_table(
        'loans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('interest_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('term_days', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('collateral_amount', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('collateral_token', sa.String(length=42), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('repaid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tx_hash', sa.String(length=66), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='chk_loan_amount'),
        sa.CheckConstraint('interest_rate >= 0 AND interest_rate <= 100', name='chk_interest_rate'),
        sa.CheckConstraint('term_days > 0', name='chk_term_days'),
        sa.CheckConstraint("status IN ('pending', 'active', 'repaid', 'defaulted', 'liquidated')", name='chk_loan_status')
    )
    op.create_index('idx_loans_wallet', 'loans', ['wallet_address'], unique=False)
    op.create_index('idx_loans_status', 'loans', ['status'], unique=False)
    op.create_index('idx_loans_created', 'loans', ['created_at'], unique=False)
    
    # Create loan_payments table
    op.create_table(
        'loan_payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('payment_type', sa.String(length=20), nullable=False),
        sa.Column('tx_hash', sa.String(length=66), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='chk_payment_amount'),
        sa.CheckConstraint("payment_type IN ('principal', 'interest', 'both')", name='chk_payment_type')
    )
    op.create_index('idx_payments_loan', 'loan_payments', ['loan_id'], unique=False)
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('tx_hash', sa.String(length=66), nullable=False),
        sa.Column('tx_type', sa.String(length=50), nullable=False),
        sa.Column('block_number', sa.Integer(), nullable=True),
        sa.Column('block_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('from_address', sa.String(length=42), nullable=True),
        sa.Column('to_address', sa.String(length=42), nullable=True),
        sa.Column('value', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('gas_used', sa.Integer(), nullable=True),
        sa.Column('gas_price', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tx_hash'),
        sa.CheckConstraint("status IN ('pending', 'success', 'failed') OR status IS NULL", name='chk_tx_status')
    )
    op.create_index('idx_transactions_wallet', 'transactions', ['wallet_address'], unique=False)
    op.create_index('idx_transactions_hash', 'transactions', ['tx_hash'], unique=True)
    op.create_index('idx_transactions_type', 'transactions', ['tx_type'], unique=False)
    op.create_index('idx_transactions_timestamp', 'transactions', ['block_timestamp'], unique=False)
    
    # Create gdpr_requests table
    op.create_table(
        'gdpr_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('request_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('export_file_path', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("request_type IN ('deletion', 'export', 'access')", name='chk_gdpr_request_type'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='chk_gdpr_status')
    )
    op.create_index('idx_gdpr_wallet', 'gdpr_requests', ['wallet_address'], unique=False)
    op.create_index('idx_gdpr_status', 'gdpr_requests', ['status'], unique=False)
    
    # Create data_retention_log table
    op.create_table(
        'data_retention_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('records_deleted', sa.Integer(), nullable=False),
        sa.Column('archived_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('retention_period_days', sa.Integer(), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('success', 'failed', 'partial') OR status IS NULL", name='chk_retention_status')
    )
    op.create_index('idx_retention_table', 'data_retention_log', ['table_name'], unique=False)
    op.create_index('idx_retention_executed', 'data_retention_log', ['executed_at'], unique=False)
    
    # Update existing tables to add foreign keys
    op.add_column('scores', sa.Column('wallet_address_fk', sa.String(length=42), nullable=True))
    op.create_foreign_key('fk_scores_user', 'scores', 'users', ['wallet_address'], ['wallet_address'])
    op.drop_column('scores', 'wallet_address_fk')
    
    op.add_column('score_history', sa.Column('wallet_address_fk', sa.String(length=42), nullable=True))
    op.create_foreign_key('fk_score_history_score', 'score_history', 'scores', ['wallet_address'], ['wallet_address'])
    op.drop_column('score_history', 'wallet_address_fk')
    
    op.add_column('user_data', sa.Column('wallet_address_fk', sa.String(length=42), nullable=True))
    op.create_foreign_key('fk_user_data_user', 'user_data', 'users', ['wallet_address'], ['wallet_address'])
    op.drop_column('user_data', 'wallet_address_fk')


def downgrade() -> None:
    # Remove foreign keys from existing tables
    op.drop_constraint('fk_user_data_user', 'user_data', type_='foreignkey')
    op.drop_constraint('fk_score_history_score', 'score_history', type_='foreignkey')
    op.drop_constraint('fk_scores_user', 'scores', type_='foreignkey')
    
    # Drop new tables
    op.drop_index('idx_retention_executed', table_name='data_retention_log')
    op.drop_index('idx_retention_table', table_name='data_retention_log')
    op.drop_table('data_retention_log')
    
    op.drop_index('idx_gdpr_status', table_name='gdpr_requests')
    op.drop_index('idx_gdpr_wallet', table_name='gdpr_requests')
    op.drop_table('gdpr_requests')
    
    op.drop_index('idx_transactions_timestamp', table_name='transactions')
    op.drop_index('idx_transactions_type', table_name='transactions')
    op.drop_index('idx_transactions_hash', table_name='transactions')
    op.drop_index('idx_transactions_wallet', table_name='transactions')
    op.drop_table('transactions')
    
    op.drop_index('idx_payments_loan', table_name='loan_payments')
    op.drop_table('loan_payments')
    
    op.drop_index('idx_loans_created', table_name='loans')
    op.drop_index('idx_loans_status', table_name='loans')
    op.drop_index('idx_loans_wallet', table_name='loans')
    op.drop_table('loans')
    
    op.drop_index(op.f('ix_users_wallet_address'), table_name='users')
    op.drop_table('users')


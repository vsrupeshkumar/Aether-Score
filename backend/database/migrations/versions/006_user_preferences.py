"""user_preferences

Revision ID: 006_user_preferences
Revises: 005_defi_integration_features
Create Date: 2025-12-18 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_user_preferences'
down_revision = '005_defi_integration_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('max_interest_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('term_days_min', sa.Integer(), nullable=True),
        sa.Column('term_days_max', sa.Integer(), nullable=True),
        sa.Column('max_loan_amount', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('preferred_collateral_tokens', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('auto_negotiate_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('auto_accept_threshold', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('wallet_address'),
        sa.CheckConstraint('max_interest_rate IS NULL OR (max_interest_rate >= 0 AND max_interest_rate <= 100)', name='chk_max_interest_rate'),
        sa.CheckConstraint('term_days_min IS NULL OR term_days_min > 0', name='chk_term_days_min'),
        sa.CheckConstraint('term_days_max IS NULL OR term_days_max >= term_days_min', name='chk_term_days_range'),
        sa.CheckConstraint('max_loan_amount IS NULL OR max_loan_amount > 0', name='chk_max_loan_amount')
    )
    
    # Create negotiation_sessions table
    op.create_table(
        'negotiation_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('loan_request_id', sa.Integer(), nullable=True),
        sa.Column('preferences_id', sa.String(length=42), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('current_offer_id', sa.Integer(), nullable=True),
        sa.Column('negotiation_history', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.ForeignKeyConstraint(['loan_request_id'], ['loan_requests.id'], ),
        sa.ForeignKeyConstraint(['preferences_id'], ['user_preferences.wallet_address'], ),
        sa.ForeignKeyConstraint(['current_offer_id'], ['loan_offers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('active', 'completed', 'cancelled', 'expired')", name='chk_negotiation_status')
    )
    op.create_index('idx_negotiation_wallet', 'negotiation_sessions', ['wallet_address'], unique=False)
    op.create_index('idx_negotiation_status', 'negotiation_sessions', ['status'], unique=False)
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='warning'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('suggested_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("severity IN ('info', 'warning', 'critical')", name='chk_alert_severity')
    )
    op.create_index('idx_alerts_wallet_read', 'alerts', ['wallet_address', 'read'], unique=False)
    op.create_index('idx_alerts_type_severity', 'alerts', ['alert_type', 'severity'], unique=False)
    op.create_index('idx_alerts_wallet_address', 'alerts', ['wallet_address'], unique=False)
    op.create_index('idx_alerts_alert_type', 'alerts', ['alert_type'], unique=False)
    op.create_index('idx_alerts_read', 'alerts', ['read'], unique=False)
    op.create_index('idx_alerts_created_at', 'alerts', ['created_at'], unique=False)
    
    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_address', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['wallet_address'], ['users.wallet_address'], ),
        sa.PrimaryKeyConstraint('wallet_address'),
        sa.CheckConstraint("email_address IS NULL OR email_address ~ '^[^@]+@[^@]+\\.[^@]+$'", name='chk_email_format')
    )


def downgrade() -> None:
    op.drop_table('notification_preferences')
    op.drop_index('idx_alerts_created_at', table_name='alerts')
    op.drop_index('idx_alerts_read', table_name='alerts')
    op.drop_index('idx_alerts_alert_type', table_name='alerts')
    op.drop_index('idx_alerts_wallet_address', table_name='alerts')
    op.drop_index('idx_alerts_type_severity', table_name='alerts')
    op.drop_index('idx_alerts_wallet_read', table_name='alerts')
    op.drop_table('alerts')
    op.drop_index('idx_negotiation_status', table_name='negotiation_sessions')
    op.drop_index('idx_negotiation_wallet', table_name='negotiation_sessions')
    op.drop_table('negotiation_sessions')
    op.drop_table('user_preferences')


#!/bin/bash
# Database migration rollback script

set -e

ENVIRONMENT=${1:-development}
REVISION=${2:-"-1"}

if [ -z "$REVISION" ]; then
    echo "Error: Revision ID required"
    echo "Usage: $0 [environment] [revision_id]"
    echo "Example: $0 production 001_initial_schema"
    exit 1
fi

ENV_FILE="environments/.env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

echo "Rolling back migration for environment: $ENVIRONMENT"
echo "Target revision: $REVISION"

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL not set"
    exit 1
fi

# Convert asyncpg URL to sync URL for Alembic
SYNC_DATABASE_URL=$(echo "$DATABASE_URL" | sed 's/postgresql+asyncpg:\/\//postgresql:\/\//')

cd backend

# Check current migration status
echo "Current migration status:"
alembic current

# Show migration history
echo ""
echo "Migration history:"
alembic history

# Confirm rollback
echo ""
echo "⚠️  WARNING: This will rollback the database schema!"
read -p "Continue with rollback? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

# Backup database before rollback
echo "Creating backup before rollback..."
../scripts/backup-db.sh "$ENVIRONMENT" || echo "Warning: Backup failed, but continuing..."

# Execute rollback
echo "Rolling back to revision: $REVISION"
export DATABASE_URL="$SYNC_DATABASE_URL"
alembic downgrade "$REVISION"

# Verify rollback
if [ $? -eq 0 ]; then
    echo "✅ Rollback completed successfully"
    echo ""
    echo "Current migration status:"
    alembic current
else
    echo "❌ Rollback failed"
    exit 1
fi


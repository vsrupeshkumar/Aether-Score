#!/bin/bash
# Database migration script

set -e

ENVIRONMENT=${1:-development}
ENV_FILE="environments/.env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

echo "Running migrations for environment: $ENVIRONMENT"

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
alembic current || echo "No migrations applied yet"

# Show pending migrations
echo ""
echo "Pending migrations:"
alembic heads

# Confirm migration
read -p "Apply migrations? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled"
    exit 0
fi

# Backup database before migration (if in production)
if [ "$ENVIRONMENT" == "production" ]; then
    echo "Creating backup before migration..."
    ../scripts/backup-db.sh production || echo "Warning: Backup failed, but continuing..."
fi

# Apply migrations
echo "Applying migrations..."
export DATABASE_URL="$SYNC_DATABASE_URL"
alembic upgrade head

# Verify migration
if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully"
    echo ""
    echo "Current migration status:"
    alembic current
else
    echo "❌ Migration failed"
    exit 1
fi


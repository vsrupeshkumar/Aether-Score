#!/bin/bash
# Database restore script with PITR support

set -e

ENVIRONMENT=${1:-production}
RESTORE_TYPE=${2:-full}  # full or pitr
BACKUP_FILE=${3:-""}
TARGET_TIME=${4:-""}  # For PITR: YYYY-MM-DD HH:MM:SS

ENV_FILE="environments/.env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

echo "⚠️  WARNING: This will restore/replace the database!"
read -p "Continue? (yes/NO): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Extract database connection details
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL not set"
    exit 1
fi

DB_URL=$(echo "$DATABASE_URL" | sed 's/postgresql+asyncpg:\/\///')
DB_USER=$(echo "$DB_URL" | cut -d: -f1)
DB_PASS=$(echo "$DB_URL" | cut -d: -f2 | cut -d@ -f1)
DB_HOST=$(echo "$DB_URL" | cut -d@ -f2 | cut -d: -f1)
DB_PORT=$(echo "$DB_URL" | cut -d: -f3 | cut -d/ -f1)
DB_NAME=$(echo "$DB_URL" | cut -d/ -f2)

export PGPASSWORD="$DB_PASS"

if [ "$RESTORE_TYPE" == "pitr" ]; then
    # Point-in-time recovery
    if [ -z "$TARGET_TIME" ]; then
        echo "Error: Target time required for PITR (format: YYYY-MM-DD HH:MM:SS)"
        exit 1
    fi
    
    echo "Performing point-in-time recovery to: $TARGET_TIME"
    echo "This requires PostgreSQL to be in recovery mode"
    echo "⚠️  This is a complex operation - ensure you have proper backups!"
    
    # Note: PITR requires:
    # 1. Base backup
    # 2. WAL archive files
    # 3. PostgreSQL configured for recovery
    # This script provides the framework - actual PITR setup varies by deployment
    
    echo "PITR restore requires manual PostgreSQL configuration"
    echo "See docs/BACKUP_STRATEGY.md for detailed PITR instructions"
    
else
    # Full restore
    if [ -z "$BACKUP_FILE" ]; then
        echo "Error: Backup file required for full restore"
        echo "Usage: $0 [environment] full [backup_file]"
        exit 1
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "Error: Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    echo "Restoring database from: $BACKUP_FILE"
    
    # Determine backup format
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        # Compressed SQL dump
        echo "Detected compressed SQL dump"
        gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
    elif [[ "$BACKUP_FILE" == *.custom ]] || [[ "$BACKUP_FILE" == *.dump ]]; then
        # Custom format (pg_dump -Fc)
        echo "Detected custom format dump"
        pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            --clean --if-exists --no-owner --no-acl \
            "$BACKUP_FILE"
    else
        # Plain SQL
        echo "Detected plain SQL dump"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ Database restored successfully"
    else
        echo "❌ Database restore failed"
        exit 1
    fi
fi


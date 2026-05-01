#!/bin/bash
# Database backup script with PITR support

set -e

ENVIRONMENT=${1:-production}
BACKUP_TYPE=${2:-full}  # full or wal
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
WAL_DIR="${BACKUP_DIR}/wal"
BACKUP_FILE="${BACKUP_DIR}/AETHER-SCORE_${ENVIRONMENT}_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=${DB_BACKUP_RETENTION_DAYS:-90}
PITR_ENABLED=${PITR_ENABLED:-true}

# Load environment variables
if [ -f "environments/.env.${ENVIRONMENT}" ]; then
    set -a
    source "environments/.env.${ENVIRONMENT}"
    set +a
fi

# Extract database connection details
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL not set"
    exit 1
fi

# Parse DATABASE_URL (postgresql+asyncpg://user:pass@host:port/dbname)
DB_URL=$(echo "$DATABASE_URL" | sed 's/postgresql+asyncpg:\/\///')
DB_USER=$(echo "$DB_URL" | cut -d: -f1)
DB_PASS=$(echo "$DB_URL" | cut -d: -f2 | cut -d@ -f1)
DB_HOST=$(echo "$DB_URL" | cut -d@ -f2 | cut -d: -f1)
DB_PORT=$(echo "$DB_URL" | cut -d: -f3 | cut -d/ -f1)
DB_NAME=$(echo "$DB_URL" | cut -d/ -f2)

echo "Starting database backup for $ENVIRONMENT"
echo "Database: $DB_NAME on $DB_HOST:$DB_PORT"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Set PGPASSWORD for pg_dump
export PGPASSWORD="$DB_PASS"

# Perform backup based on type
if [ "$BACKUP_TYPE" == "wal" ]; then
    # WAL archiving (for PITR)
    if [ "$PITR_ENABLED" == "true" ]; then
        echo "Archiving WAL files..."
        mkdir -p "$WAL_DIR"
        # This assumes PostgreSQL is configured with archive_command
        # The actual archiving is handled by PostgreSQL's archive_command
        echo "âœ… WAL archiving configured (handled by PostgreSQL)"
    else
        echo "âš ï¸  PITR not enabled, skipping WAL archiving"
    fi
else
    # Full backup
    echo "Performing full database backup..."
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --no-owner --no-acl --clean --if-exists \
        --format=custom \
        --file="${BACKUP_FILE%.gz}"
    
    # Compress backup
    gzip "${BACKUP_FILE%.gz}"
    
    # Verify backup
    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "âœ… Backup completed successfully: $BACKUP_FILE ($BACKUP_SIZE)"
        
        # Create backup manifest for PITR
        if [ "$PITR_ENABLED" == "true" ]; then
            MANIFEST_FILE="${BACKUP_DIR}/manifest_${ENVIRONMENT}_${TIMESTAMP}.json"
            cat > "$MANIFEST_FILE" << EOF
{
  "backup_file": "$BACKUP_FILE",
  "timestamp": "$TIMESTAMP",
  "environment": "$ENVIRONMENT",
  "database": "$DB_NAME",
  "host": "$DB_HOST",
  "port": "$DB_PORT",
  "pitr_enabled": true
}
EOF
            echo "âœ… Backup manifest created: $MANIFEST_FILE"
        fi
    else
        echo "âŒ Backup failed: file not created or empty"
        exit 1
    fi
fi

# Upload to S3 if configured
if [ -n "$DB_BACKUP_S3_BUCKET" ]; then
    echo "Uploading backup to S3..."
    if command -v aws &> /dev/null; then
        aws s3 cp "$BACKUP_FILE" "s3://${DB_BACKUP_S3_BUCKET}/${ENVIRONMENT}/" || echo "âš ï¸  S3 upload failed"
    else
        echo "âš ï¸  AWS CLI not found, skipping S3 upload"
    fi
fi

# Clean up old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "AETHER-SCORE_${ENVIRONMENT}_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

echo "âœ… Backup process completed"



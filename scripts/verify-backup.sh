#!/bin/bash
# Backup verification script

set -e

BACKUP_FILE=${1:-""}

if [ -z "$BACKUP_FILE" ]; then
    echo "Error: Backup file required"
    echo "Usage: $0 [backup_file]"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Verifying backup: $BACKUP_FILE"

# Check file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup size: $FILE_SIZE"

if [ ! -s "$BACKUP_FILE" ]; then
    echo "❌ Backup file is empty"
    exit 1
fi

# Check file format
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Checking compressed SQL dump..."
    if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
        echo "✅ Backup file is valid compressed SQL"
        
        # Extract and check SQL syntax (basic check)
        echo "Checking SQL syntax..."
        if gunzip -c "$BACKUP_FILE" | head -100 | grep -q "CREATE\|INSERT\|COPY"; then
            echo "✅ Backup contains valid SQL statements"
        else
            echo "⚠️  Warning: Backup may not contain expected SQL statements"
        fi
    else
        echo "❌ Backup file is corrupted (invalid gzip)"
        exit 1
    fi
elif [[ "$BACKUP_FILE" == *.custom ]] || [[ "$BACKUP_FILE" == *.dump ]]; then
    echo "Checking custom format dump..."
    if pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1; then
        echo "✅ Backup file is valid custom format"
        
        # List contents
        echo "Backup contents:"
        pg_restore --list "$BACKUP_FILE" | head -20
    else
        echo "❌ Backup file is corrupted (invalid custom format)"
        exit 1
    fi
else
    echo "Checking plain SQL dump..."
    if head -100 "$BACKUP_FILE" | grep -q "CREATE\|INSERT\|COPY"; then
        echo "✅ Backup appears to be valid SQL"
    else
        echo "⚠️  Warning: Backup may not be valid SQL"
    fi
fi

# Check for critical tables
echo "Checking for critical tables..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    TABLES=$(gunzip -c "$BACKUP_FILE" | grep -i "CREATE TABLE" | head -10)
else
    TABLES=$(grep -i "CREATE TABLE" "$BACKUP_FILE" | head -10)
fi

if echo "$TABLES" | grep -qi "users\|scores\|loans"; then
    echo "✅ Backup contains critical tables"
else
    echo "⚠️  Warning: Backup may be missing critical tables"
fi

echo ""
echo "✅ Backup verification completed"
echo "Backup file: $BACKUP_FILE"
echo "Size: $FILE_SIZE"


#!/bin/bash
# Archive old data to cold storage

set -e

ENVIRONMENT=${1:-production}
ENV_FILE="environments/.env.${ENVIRONMENT}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found"
    exit 1
fi

echo "Archiving old data for environment: $ENVIRONMENT"

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Check S3 bucket configuration
if [ -z "$DB_BACKUP_S3_BUCKET" ]; then
    echo "Error: DB_BACKUP_S3_BUCKET not set"
    exit 1
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not found"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_DIR="/tmp/archive_${TIMESTAMP}"
mkdir -p "$ARCHIVE_DIR"

cd backend

# Archive old score history
echo "Archiving old score history..."
python3 << EOF
import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
sys.path.insert(0, os.getcwd())

from database.connection import get_db_session
from database.models import ScoreHistory
from sqlalchemy import select

async def archive_score_history():
    cutoff_date = datetime.utcnow() - timedelta(days=365)
    archive_file = "$ARCHIVE_DIR/score_history.json"
    
    async with get_db_session() as session:
        result = await session.execute(
            select(ScoreHistory).where(ScoreHistory.timestamp < cutoff_date)
        )
        records = result.scalars().all()
        
        data = [{
            "id": r.id,
            "wallet_address": r.wallet_address,
            "score": r.score,
            "risk_band": r.risk_band,
            "timestamp": r.timestamp.isoformat()
        } for r in records]
        
        with open(archive_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Archived {len(data)} score history records to {archive_file}")
        return len(data)

asyncio.run(archive_score_history())
EOF

# Archive old transactions
echo "Archiving old transactions..."
python3 << EOF
import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
sys.path.insert(0, os.getcwd())

from database.connection import get_db_session
from database.models import Transaction
from sqlalchemy import select

async def archive_transactions():
    cutoff_date = datetime.utcnow() - timedelta(days=365)
    archive_file = "$ARCHIVE_DIR/transactions.json"
    
    async with get_db_session() as session:
        result = await session.execute(
            select(Transaction).where(Transaction.block_timestamp < cutoff_date)
        )
        records = result.scalars().all()
        
        data = [{
            "id": r.id,
            "wallet_address": r.wallet_address,
            "tx_hash": r.tx_hash,
            "tx_type": r.tx_type,
            "block_number": r.block_number,
            "block_timestamp": r.block_timestamp.isoformat() if r.block_timestamp else None,
            "value": str(r.value) if r.value else None,
            "status": r.status,
            "metadata": r.metadata
        } for r in records]
        
        with open(archive_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Archived {len(data)} transaction records to {archive_file}")
        return len(data)

asyncio.run(archive_transactions())
EOF

# Upload to S3
echo "Uploading archives to S3..."
aws s3 cp "$ARCHIVE_DIR" "s3://${DB_BACKUP_S3_BUCKET}/archives/${ENVIRONMENT}/${TIMESTAMP}/" --recursive

if [ $? -eq 0 ]; then
    echo "✅ Archives uploaded successfully"
    rm -rf "$ARCHIVE_DIR"
else
    echo "❌ Failed to upload archives"
    exit 1
fi


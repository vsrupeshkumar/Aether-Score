# Data Retention Policy

This document outlines the data retention policy for AETHER-SCORE.

## Overview

AETHER-SCORE implements a data retention policy to comply with regulations, optimize storage, and maintain data quality.

## Retention Periods

### Score History
- **Retention Period**: 1 year (365 days)
- **Action**: Archive to cold storage after retention period
- **Rationale**: Historical score data is useful for trend analysis but doesn't need to be in active database

### Transaction History
- **Retention Period**: 1 year (365 days)
- **Action**: Archive to cold storage after retention period
- **Rationale**: Transaction data is primarily needed for recent activity analysis

### User Data
- **Retention Period**: Until deletion requested
- **Action**: Soft delete when user requests deletion (30-day grace period)
- **Rationale**: User data is retained until explicit deletion request for GDPR compliance

### Audit Logs
- **Retention Period**: 2 years (730 days)
- **Action**: Archive to cold storage after retention period
- **Rationale**: Audit logs are required for compliance and security investigations

### Backup Retention
- **Production**: 90 days
- **Staging**: 30 days
- **Development**: 7 days

## Implementation

### Automated Cleanup

Data retention is enforced through:
- **Kubernetes CronJob**: Runs daily at 2 AM UTC
- **Retention Service**: `backend/services/retention.py`
- **Archival Service**: Archives old data to S3 before deletion

### Manual Cleanup

To manually run retention cleanup:
```bash
cd backend
python -c "import asyncio; from services.retention import DataRetentionService; asyncio.run(DataRetentionService().cleanup_all())"
```

### Archival Process

1. **Identify Old Data**: Records older than retention period
2. **Archive to S3**: Export to JSON and upload to S3 Glacier
3. **Delete from Database**: Remove archived records
4. **Log Action**: Record in `data_retention_log` table

## Configuration

Environment variables:
```bash
RETENTION_SCORE_HISTORY_DAYS=365
RETENTION_TRANSACTIONS_DAYS=365
RETENTION_AUDIT_LOGS_DAYS=730
DB_BACKUP_S3_BUCKET=AETHER-SCORE-backups
```

## Monitoring

Retention actions are logged in the `data_retention_log` table:
- Table name
- Records deleted
- Records archived
- Retention period
- Execution timestamp
- Status (success/failed/partial)

## Compliance

This retention policy is designed to:
- Comply with GDPR requirements
- Meet financial data retention requirements
- Optimize database performance
- Reduce storage costs

## Exceptions

Some data may be retained longer for:
- Active legal investigations
- Regulatory requirements
- User consent for extended retention

## Data Recovery

Archived data can be restored from S3:
1. Download archive from S3
2. Import JSON data back to database
3. Verify data integrity

See `docs/DATA_ARCHIVAL.md` for detailed recovery procedures.



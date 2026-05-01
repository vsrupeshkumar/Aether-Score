# Backup Strategy

This document outlines the backup and recovery strategy for AETHER-SCORE.

## Overview

AETHER-SCORE implements a comprehensive backup strategy with:
- Automated daily backups
- Point-in-time recovery (PITR) support
- Backup verification
- Multiple retention periods
- S3 off-site storage

## Backup Types

### 1. Full Backups

**Schedule**: Daily at 2 AM UTC

**Format**: PostgreSQL custom format (compressed)

**Retention**:
- Production: 90 days
- Staging: 30 days
- Development: 7 days

**Storage**:
- Local: `/backups`
- Remote: S3 bucket (if configured)

### 2. WAL Archiving (PITR)

**Purpose**: Enable point-in-time recovery

**Configuration**: Requires PostgreSQL `archive_mode = on`

**Archive Location**: `/backups/wal`

**Retention**: 7 days (configurable)

## Backup Process

### Automated Backups

Backups are performed by Kubernetes CronJob:
- **Schedule**: `0 2 * * *` (daily at 2 AM)
- **Script**: `scripts/backup-db.sh`
- **Manifest**: `k8s/postgres-backup-cronjob.yaml`

### Manual Backups

```bash
# Full backup
./scripts/backup-db.sh production full

# WAL archiving check
./scripts/backup-db.sh production wal
```

## Backup Verification

### Automated Verification

Backups are verified after creation:
- File size check
- Compression integrity
- SQL syntax validation
- Critical table presence

### Manual Verification

```bash
./scripts/verify-backup.sh /backups/AETHER-SCORE_production_20250101_020000.sql.gz
```

## Restore Procedures

### Full Restore

```bash
# Restore from backup file
./scripts/restore-db.sh production full /backups/AETHER-SCORE_production_20250101_020000.sql.gz
```

### Point-in-Time Recovery (PITR)

PITR requires:
1. Base backup
2. WAL archive files
3. PostgreSQL recovery configuration

**Steps**:
1. Restore base backup
2. Configure `recovery.conf` or `postgresql.conf`:
   ```conf
   restore_command = 'cp /backups/wal/%f %p'
   recovery_target_time = '2025-01-01 12:00:00'
   ```
3. Start PostgreSQL in recovery mode
4. PostgreSQL will replay WAL files to target time

**Note**: PITR is complex and requires careful PostgreSQL configuration. See PostgreSQL documentation for details.

## Backup Storage

### Local Storage

- **Path**: `/backups`
- **Format**: `AETHER-SCORE_{environment}_{timestamp}.sql.gz`
- **Manifest**: `manifest_{environment}_{timestamp}.json`

### S3 Storage

If `DB_BACKUP_S3_BUCKET` is configured:
- Backups are automatically uploaded to S3
- Path: `s3://{bucket}/{environment}/`
- Lifecycle policies can be configured for cost optimization

## Configuration

### Environment Variables

```bash
# Backup configuration
DB_BACKUP_RETENTION_DAYS=90
DB_BACKUP_S3_BUCKET=AETHER-SCORE-backups
PITR_ENABLED=true

# PostgreSQL WAL archiving (in postgresql.conf)
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
wal_level = replica
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: AETHER-SCORE-secrets
data:
  DB_HOST: <base64>
  DB_PORT: <base64>
  DB_USER: <base64>
  DB_PASSWORD: <base64>
  DB_NAME: <base64>
```

## Monitoring

### Backup Status

Check CronJob status:
```bash
kubectl get cronjob postgres-backup -n AETHER-SCORE
kubectl get jobs -n AETHER-SCORE | grep postgres-backup
```

### Backup Logs

```bash
kubectl logs -n AETHER-SCORE job/postgres-backup-{timestamp}
```

### Alerts

Set up alerts for:
- Backup failures
- Backup size anomalies
- S3 upload failures
- Disk space warnings

## Disaster Recovery

### Recovery Time Objective (RTO)

- **Target**: < 4 hours
- **Includes**: Backup restore + service restart

### Recovery Point Objective (RPO)

- **Target**: < 24 hours (daily backups)
- **With PITR**: < 1 hour (WAL archiving)

### Recovery Procedures

1. **Identify latest backup**
   ```bash
   ls -lt /backups/AETHER-SCORE_production_*.sql.gz | head -1
   ```

2. **Verify backup integrity**
   ```bash
   ./scripts/verify-backup.sh {backup_file}
   ```

3. **Restore database**
   ```bash
   ./scripts/restore-db.sh production full {backup_file}
   ```

4. **Verify restore**
   - Check database connectivity
   - Verify critical tables
   - Test application functionality

5. **Update services**
   - Restart backend services
   - Verify API endpoints
   - Monitor for errors

## Best Practices

1. **Test Restores Regularly**
   - Monthly restore tests
   - Document restore procedures
   - Train team on recovery

2. **Monitor Backup Health**
   - Automated verification
   - Alert on failures
   - Regular backup audits

3. **Off-Site Storage**
   - Always use S3 or similar
   - Configure lifecycle policies
   - Test S3 restore procedures

4. **Documentation**
   - Keep restore procedures updated
   - Document recovery scenarios
   - Maintain runbooks

## Troubleshooting

### Backup Fails

1. Check database connectivity
2. Verify disk space
3. Check PostgreSQL logs
4. Review CronJob logs

### Restore Fails

1. Verify backup file integrity
2. Check database permissions
3. Ensure sufficient disk space
4. Review PostgreSQL logs

### PITR Issues

1. Verify WAL archiving is enabled
2. Check WAL files are available
3. Verify recovery configuration
4. Check PostgreSQL logs

## References

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [PostgreSQL PITR Guide](https://www.postgresql.org/docs/current/continuous-archiving.html)
- [AWS S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)



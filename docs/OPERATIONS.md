# Operations Runbook

This runbook provides step-by-step procedures for common operational tasks, incident response, and troubleshooting.

## Table of Contents

- [Common Operations](#common-operations)
- [Incident Response](#incident-response)
- [Monitoring & Alerts](#monitoring--alerts)
- [Database Operations](#database-operations)
- [Backup & Recovery](#backup--recovery)
- [Performance Tuning](#performance-tuning)

## Common Operations

### Service Restart

```bash
# Restart backend
kubectl rollout restart deployment/backend -n AETHER-SCORE-prod

# Restart frontend
kubectl rollout restart deployment/frontend -n AETHER-SCORE-prod

# Restart workers
kubectl rollout restart deployment/worker -n AETHER-SCORE-prod

# Verify restart
kubectl rollout status deployment/backend -n AETHER-SCORE-prod
```

### Scaling Services

```bash
# Scale backend
kubectl scale deployment/backend --replicas=5 -n AETHER-SCORE-prod

# Scale frontend
kubectl scale deployment/frontend --replicas=3 -n AETHER-SCORE-prod

# Scale workers
kubectl scale deployment/worker --replicas=10 -n AETHER-SCORE-prod
```

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n AETHER-SCORE-prod --tail=100

# Frontend logs
kubectl logs -f deployment/frontend -n AETHER-SCORE-prod --tail=100

# Worker logs
kubectl logs -f deployment/worker -n AETHER-SCORE-prod --tail=100

# All logs
kubectl logs -f -l app=AETHER-SCORE -n AETHER-SCORE-prod
```

### Check Service Health

```bash
# Health check
curl https://api.AETHER-SCORE.io/health

# Readiness check
curl https://api.AETHER-SCORE.io/health/ready

# Metrics
curl https://api.AETHER-SCORE.io/metrics
```

## Incident Response

### Severity Levels

- **P0 - Critical**: Service down, data loss, security breach
- **P1 - High**: Major feature broken, significant performance degradation
- **P2 - Medium**: Minor feature broken, moderate performance issues
- **P3 - Low**: Cosmetic issues, minor bugs

### Incident Response Process

1. **Acknowledge**: Acknowledge the incident in the incident channel
2. **Assess**: Determine severity and impact
3. **Mitigate**: Take immediate steps to mitigate impact
4. **Communicate**: Update stakeholders on status
5. **Resolve**: Fix the root cause
6. **Post-Mortem**: Document lessons learned

### P0 - Critical Incident

#### Service Down

```bash
# 1. Check service status
kubectl get pods -n AETHER-SCORE-prod

# 2. Check logs for errors
kubectl logs -f deployment/backend -n AETHER-SCORE-prod --tail=200

# 3. Check database connectivity
kubectl exec -it deployment/backend -n AETHER-SCORE-prod -- \
  python -c "from database.connection import get_db_pool; import asyncio; asyncio.run(get_db_pool())"

# 4. Restart services if needed
kubectl rollout restart deployment/backend -n AETHER-SCORE-prod

# 5. If restart doesn't work, rollback
kubectl rollout undo deployment/backend -n AETHER-SCORE-prod
```

#### Database Issues

```bash
# 1. Check database status
kubectl get pods -l app=postgres -n AETHER-SCORE-prod

# 2. Check database connections
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'AETHER-SCORE';
"

# 3. Check for locks
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT * FROM pg_locks WHERE NOT granted;
"

# 4. Kill long-running queries if needed
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE datname = 'AETHER-SCORE' AND state = 'idle in transaction';
"
```

#### Security Breach

1. **Immediate Actions**:
   - Rotate all API keys and secrets
   - Revoke compromised credentials
   - Enable additional monitoring
   - Notify security team

2. **Investigation**:
   - Review access logs
   - Check for unauthorized changes
   - Identify attack vector

3. **Remediation**:
   - Patch vulnerabilities
   - Update security policies
   - Conduct security audit

### P1 - High Priority Incident

#### Performance Degradation

```bash
# 1. Check resource usage
kubectl top pods -n AETHER-SCORE-prod

# 2. Check slow queries
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"

# 3. Check Redis memory
kubectl exec -it redis-pod -- redis-cli INFO memory

# 4. Scale services if needed
kubectl scale deployment/backend --replicas=10 -n AETHER-SCORE-prod
```

#### High Error Rate

```bash
# 1. Check error logs
kubectl logs -f deployment/backend -n AETHER-SCORE-prod | grep ERROR

# 2. Check Sentry for errors
# Visit: https://sentry.io/organizations/AETHER-SCORE/issues/

# 3. Check metrics
curl https://api.AETHER-SCORE.io/metrics | grep error_rate

# 4. Review recent deployments
kubectl rollout history deployment/backend -n AETHER-SCORE-prod
```

## Monitoring & Alerts

### Key Metrics to Monitor

- **API Response Time**: P50, P95, P99
- **Error Rate**: 4xx, 5xx errors
- **Database Connections**: Active connections, pool usage
- **Redis Memory**: Memory usage, evictions
- **Blockchain RPC**: Success rate, latency
- **Queue Depth**: RQ queue length

### Alert Thresholds

- **API Response Time P95 > 2s**: Warning
- **API Response Time P95 > 5s**: Critical
- **Error Rate > 1%**: Warning
- **Error Rate > 5%**: Critical
- **Database Connections > 80%**: Warning
- **Database Connections > 95%**: Critical
- **Redis Memory > 80%**: Warning
- **Redis Memory > 95%**: Critical

### Setting Up Alerts

```yaml
# prometheus-alerts.yaml
groups:
  - name: AETHER-SCORE
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        annotations:
          summary: "High response time detected"
```

## Database Operations

### Backup

```bash
# Manual backup
kubectl exec -it postgres-pod -- \
  pg_dump -U AETHER-SCORE AETHER-SCORE > backup-$(date +%Y%m%d-%H%M%S).sql

# Automated backup (CronJob)
kubectl apply -f k8s/overlays/prod/backup-cronjob.yaml -n AETHER-SCORE-prod
```

### Restore

```bash
# Restore from backup
kubectl exec -i postgres-pod -- \
  psql -U AETHER-SCORE AETHER-SCORE < backup-20240101-120000.sql

# Verify restore
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT count(*) FROM users;
SELECT count(*) FROM scores;
"
```

### Migration

```bash
# Run migrations
kubectl run alembic-migration \
  --image=AETHER-SCORE/backend:latest \
  --restart=Never \
  --command -- alembic upgrade head \
  -n AETHER-SCORE-prod

# Rollback migration
kubectl run alembic-rollback \
  --image=AETHER-SCORE/backend:latest \
  --restart=Never \
  --command -- alembic downgrade -1 \
  -n AETHER-SCORE-prod
```

### Maintenance

```bash
# Vacuum database
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "VACUUM ANALYZE;"

# Reindex
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "REINDEX DATABASE AETHER-SCORE;"

# Check table sizes
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## Backup & Recovery

### Backup Strategy

- **Database**: Daily full backups, hourly incremental backups
- **Secrets**: Encrypted backups to secure storage
- **Configuration**: Version-controlled in Git
- **Backup Retention**: 90 days (configurable via `DB_BACKUP_RETENTION_DAYS`)
- **Backup Storage**: Local + S3 (if configured)

### Backup Procedures

#### Manual Backup

```bash
# Using backup script
./scripts/backup-db.sh production full

# Or directly with kubectl
kubectl exec -it postgres-pod -- \
  pg_dump -U AETHER-SCORE AETHER-SCORE > backup-$(date +%Y%m%d-%H%M%S).sql
```

#### Automated Backups

```bash
# Apply CronJob for automated backups
kubectl apply -f k8s/postgres-backup-cronjob.yaml -n AETHER-SCORE-prod

# Check backup job status
kubectl get cronjob postgres-backup -n AETHER-SCORE-prod
kubectl get jobs -l job-name=postgres-backup -n AETHER-SCORE-prod
```

#### Verify Backup

```bash
# Verify backup integrity
./scripts/verify-backup.sh backup-20240101-120000.sql.gz

# Check backup contents
gunzip -c backup-20240101-120000.sql.gz | head -100
```

### Recovery Procedures

#### Database Recovery

**Step 1: Stop Services**
```bash
# Stop backend to prevent new writes
kubectl scale deployment/backend --replicas=0 -n AETHER-SCORE-prod
kubectl scale deployment/worker --replicas=0 -n AETHER-SCORE-prod
```

**Step 2: Restore Database**
```bash
# Option A: Restore from local backup
kubectl exec -i postgres-pod -- \
  psql -U AETHER-SCORE AETHER-SCORE < backup-20240101-120000.sql

# Option B: Restore from S3
aws s3 cp s3://AETHER-SCORE-backups/production/backup-20240101-120000.sql.gz - | \
  gunzip | kubectl exec -i postgres-pod -- psql -U AETHER-SCORE AETHER-SCORE

# Option C: Restore compressed backup
gunzip -c backup-20240101-120000.sql.gz | \
  kubectl exec -i postgres-pod -- psql -U AETHER-SCORE AETHER-SCORE
```

**Step 3: Verify Restore**
```bash
# Check table counts
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT 
    'users' as table_name, count(*) FROM users
UNION ALL
SELECT 'scores', count(*) FROM scores
UNION ALL
SELECT 'loans', count(*) FROM loans
UNION ALL
SELECT 'transactions', count(*) FROM transactions;
"

# Check latest records
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT wallet_address, score, last_updated 
FROM scores 
ORDER BY last_updated DESC 
LIMIT 10;
"
```

**Step 4: Restart Services**
```bash
# Restart services
kubectl scale deployment/backend --replicas=3 -n AETHER-SCORE-prod
kubectl scale deployment/worker --replicas=5 -n AETHER-SCORE-prod

# Verify services are healthy
kubectl rollout status deployment/backend -n AETHER-SCORE-prod
curl https://api.AETHER-SCORE.io/health/ready
```

#### Point-in-Time Recovery (PITR)

**Prerequisites**: WAL archiving must be enabled

**Step 1: Identify Recovery Point**
```bash
RECOVERY_TIME="2024-01-01 12:00:00"
```

**Step 2: Find Base Backup**
```bash
# List available backups
ls -lh /backups/AETHER-SCORE_production_*.sql.gz

# Find backup closest to recovery time
BACKUP_FILE=$(ls -t /backups/AETHER-SCORE_production_*.sql.gz | head -1)
```

**Step 3: Restore Base Backup**
```bash
# Restore base backup
gunzip -c "$BACKUP_FILE" | \
  kubectl exec -i postgres-pod -- psql -U AETHER-SCORE AETHER-SCORE
```

**Step 4: Restore WAL Files**
```bash
# Create recovery.conf (PostgreSQL 12+ uses recovery.signal)
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
ALTER SYSTEM SET restore_command = 'cp /wal_archive/%f %p';
ALTER SYSTEM SET recovery_target_time = '$RECOVERY_TIME';
SELECT pg_reload_conf();
"

# Restart PostgreSQL to apply recovery
kubectl rollout restart statefulset/postgres -n AETHER-SCORE-prod
```

**Step 5: Verify Recovery**
```bash
# Check recovery status
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT pg_is_in_recovery();
SELECT now();
"

# Verify data at recovery point
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT max(last_updated) FROM scores;
"
```

#### Disaster Recovery

**Full Environment Recovery**

```bash
# 1. Restore database
./scripts/backup-db.sh production restore backup-20240101-120000.sql.gz

# 2. Restore secrets (from secure storage)
kubectl create secret generic api-secrets \
  --from-literal=sentry-dsn=<sentry-dsn> \
  --from-literal=jwt-secret=<jwt-secret> \
  -n AETHER-SCORE-prod

# 3. Restore configuration
kubectl apply -f k8s/base/configmap.yaml -n AETHER-SCORE-prod

# 4. Deploy services
kubectl apply -k k8s/overlays/prod/ -n AETHER-SCORE-prod

# 5. Verify everything
kubectl get all -n AETHER-SCORE-prod
curl https://api.AETHER-SCORE.io/health
```

### Backup Testing

**Test Restore Procedure** (Monthly)

```bash
# 1. Create test database
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
CREATE DATABASE AETHER-SCORE_test_restore;
"

# 2. Restore backup to test database
gunzip -c backup-20240101-120000.sql.gz | \
  kubectl exec -i postgres-pod -- psql -U AETHER-SCORE AETHER-SCORE_test_restore

# 3. Verify data integrity
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE AETHER-SCORE_test_restore -c "
SELECT count(*) FROM users;
SELECT count(*) FROM scores;
"

# 4. Cleanup
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
DROP DATABASE AETHER-SCORE_test_restore;
"
```

## Performance Tuning

### Database Optimization

```bash
# Analyze query performance
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
"

# Create indexes for slow queries
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
CREATE INDEX CONCURRENTLY idx_users_wallet_address ON users(wallet_address);
"
```

### Redis Optimization

```bash
# Check memory usage
kubectl exec -it redis-pod -- redis-cli INFO memory

# Check key distribution
kubectl exec -it redis-pod -- redis-cli --scan --pattern "*" | head -100

# Optimize memory
kubectl exec -it redis-pod -- redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Application Optimization

```bash
# Enable query caching
# Update backend config to enable Redis caching

# Optimize connection pooling
# Update DATABASE_POOL_SIZE in ConfigMap

# Enable CDN for static assets
# Configure CDN in frontend deployment
```

## Support Contacts

- **On-Call Engineer**: [Contact Info]
- **Database Admin**: [Contact Info]
- **Security Team**: security@AETHER-SCORE.io
- **DevOps Team**: devops@AETHER-SCORE.io

## References

- [Troubleshooting Guide](runbook/troubleshooting.md)
- [Database Recovery](runbook/database-recovery.md)
- [Incident Response](runbook/incident-response.md)
- [Common Issues](runbook/common-issues.md)



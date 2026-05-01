# Troubleshooting Guide

## General Troubleshooting Steps

### 1. Check Service Status

```bash
# Kubernetes
kubectl get all -n AETHER-SCORE-prod

# Docker Compose
docker-compose ps
```

### 2. Check Logs

```bash
# Kubernetes
kubectl logs -f deployment/backend -n AETHER-SCORE-prod
kubectl logs -f deployment/frontend -n AETHER-SCORE-prod

# Docker Compose
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. Check Health Endpoints

```bash
# Liveness
curl http://localhost:8000/health

# Readiness
curl http://localhost:8000/health/ready

# Metrics
curl http://localhost:8000/metrics
```

### 4. Check Resource Usage

```bash
# Kubernetes
kubectl top pods -n AETHER-SCORE-prod
kubectl top nodes

# Docker
docker stats
```

## Database Troubleshooting

### Connection Issues

```bash
# Test connection
kubectl exec -it backend-pod -- python -c "
from database.connection import get_db_pool
import asyncio
async def test():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval('SELECT 1')
        print(f'Connection successful: {result}')
asyncio.run(test())
"
```

### Query Performance

```bash
# Enable query logging
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
ALTER DATABASE AETHER-SCORE SET log_min_duration_statement = 1000;
"

# Check slow queries
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

### Database Size

```bash
# Check database size
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "
SELECT pg_size_pretty(pg_database_size('AETHER-SCORE'));
"

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

## Redis Troubleshooting

### Connection Test

```bash
# Test Redis connection
kubectl exec -it redis-pod -- redis-cli ping

# Check Redis info
kubectl exec -it redis-pod -- redis-cli INFO
```

### Memory Usage

```bash
# Check memory
kubectl exec -it redis-pod -- redis-cli INFO memory

# Check keys
kubectl exec -it redis-pod -- redis-cli DBSIZE
```

### Clear Cache

```bash
# Flush all (use with caution)
kubectl exec -it redis-pod -- redis-cli FLUSHALL

# Flush current database
kubectl exec -it redis-pod -- redis-cli FLUSHDB
```

## Blockchain Troubleshooting

### RPC Connection

```bash
# Test RPC endpoint
curl -X POST https://rpc1testnet.qie.digital/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": 1
  }'
```

### Contract Verification

```bash
# Check contract code
kubectl exec -it backend-pod -- python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://rpc1testnet.qie.digital/'))
code = w3.eth.get_code('0x...')
print(f'Contract code length: {len(code)}')
"
```

### Transaction Status

```bash
# Check transaction
kubectl exec -it backend-pod -- python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://rpc1testnet.qie.digital/'))
tx = w3.eth.get_transaction('0x...')
print(tx)
"
```

## Application Troubleshooting

### Python Debugging

```bash
# Interactive Python shell
kubectl exec -it backend-pod -- python

# Run specific function
kubectl exec -it backend-pod -- python -c "
from services.scoring import ScoringService
service = ScoringService()
print(service)
"
```

### Check Configuration

```bash
# View environment variables
kubectl exec -it backend-pod -- env | grep -E 'DATABASE|REDIS|QIE'

# View ConfigMap
kubectl get configmap -n AETHER-SCORE-prod -o yaml
```

## Network Troubleshooting

### Service Discovery

```bash
# Check services
kubectl get svc -n AETHER-SCORE-prod

# Test service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://backend:8000/health
```

### DNS Resolution

```bash
# Test DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup backend.AETHER-SCORE-prod.svc.cluster.local
```

## Performance Troubleshooting

### Profiling

```bash
# Python profiling
kubectl exec -it backend-pod -- python -m cProfile -o profile.stats -m app

# Analyze profile
kubectl exec -it backend-pod -- python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
"
```

### Memory Profiling

```bash
# Check memory usage
kubectl exec -it backend-pod -- python -c "
import tracemalloc
tracemalloc.start()
# Run your code
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"
```

## Recovery Procedures

### Restart Services

```bash
# Kubernetes
kubectl rollout restart deployment/backend -n AETHER-SCORE-prod
kubectl rollout restart deployment/frontend -n AETHER-SCORE-prod

# Docker Compose
docker-compose restart backend
docker-compose restart frontend
```

### Rollback Deployment

```bash
# Kubernetes
kubectl rollout undo deployment/backend -n AETHER-SCORE-prod

# Check rollout history
kubectl rollout history deployment/backend -n AETHER-SCORE-prod
```

### Database Recovery

```bash
# Restore from backup
kubectl exec -i postgres-pod -- psql -U AETHER-SCORE AETHER-SCORE < backup.sql

# Point-in-time recovery (if enabled)
# Contact DBA for PITR procedures
```



# Common Issues Runbook

## API Issues

### Issue: 500 Internal Server Error

**Symptoms:**
- API returns 500 status
- Error logs show exceptions

**Diagnosis:**
```bash
# Check backend logs
kubectl logs -f deployment/backend -n AETHER-SCORE-prod

# Check Sentry for error details
# Check Prometheus for error rates
```

**Solutions:**
1. Check database connectivity
2. Verify Redis connection
3. Check RPC endpoint availability
4. Review recent deployments
5. Check resource limits (CPU/Memory)

**Resolution:**
```bash
# Restart backend
kubectl rollout restart deployment/backend -n AETHER-SCORE-prod

# Check pod status
kubectl get pods -n AETHER-SCORE-prod
```

### Issue: Rate Limit Exceeded

**Symptoms:**
- 429 Too Many Requests
- Rate limit error messages

**Diagnosis:**
```bash
# Check rate limit metrics
curl http://localhost:8000/metrics | grep rate_limit

# Check Redis for rate limit keys
kubectl exec -it redis-pod -- redis-cli KEYS "rate_limit:*"
```

**Solutions:**
1. Increase rate limit threshold
2. Implement client-side rate limiting
3. Use API key for higher limits
4. Check for DDoS attacks

### Issue: Database Connection Errors

**Symptoms:**
- "Connection refused" errors
- "Too many connections" errors
- Timeout errors

**Diagnosis:**
```bash
# Check database status
kubectl get pods -l app=postgres -n AETHER-SCORE-prod

# Check connection pool
kubectl exec -it backend-pod -- python -c "from database.connection import get_db_pool; print(get_db_pool())"
```

**Solutions:**
1. Increase connection pool size
2. Check database resource limits
3. Verify network policies
4. Check database logs

## Frontend Issues

### Issue: Build Failures

**Symptoms:**
- Build errors in CI/CD
- TypeScript errors
- Missing dependencies

**Diagnosis:**
```bash
# Check build logs
docker-compose logs frontend

# Run build locally
cd frontend && npm run build
```

**Solutions:**
1. Clear node_modules and reinstall
2. Update dependencies
3. Fix TypeScript errors
4. Check environment variables

### Issue: Service Worker Not Working

**Symptoms:**
- Offline mode not working
- Cache not updating

**Diagnosis:**
```bash
# Check service worker registration
# Browser DevTools > Application > Service Workers
```

**Solutions:**
1. Clear browser cache
2. Update service worker version
3. Check service worker registration
4. Verify offline.html exists

## Blockchain Issues

### Issue: Transaction Failures

**Symptoms:**
- Transactions reverting
- Gas estimation failures
- Network errors

**Diagnosis:**
```bash
# Check RPC endpoint
curl -X POST https://rpc1testnet.qie.digital/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Check contract addresses
kubectl get configmap -n AETHER-SCORE-prod
```

**Solutions:**
1. Verify RPC endpoint is accessible
2. Check contract addresses
3. Verify private key is correct
4. Check gas prices
5. Verify network ID

### Issue: Contract Call Failures

**Symptoms:**
- Contract calls failing
- "Contract not found" errors

**Diagnosis:**
```bash
# Verify contract addresses
kubectl exec -it backend-pod -- python -c "from services.blockchain import BlockchainService; print(BlockchainService().contract_addresses)"
```

**Solutions:**
1. Verify contract addresses in environment
2. Check contract deployment
3. Verify ABI matches contract
4. Check network configuration

## Database Issues

### Issue: Slow Queries

**Symptoms:**
- High query latency
- Timeout errors
- High CPU usage

**Diagnosis:**
```bash
# Check slow queries
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Check indexes
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "\d+ scores"
```

**Solutions:**
1. Add missing indexes
2. Optimize queries
3. Increase connection pool
4. Add read replicas
5. Enable query caching

### Issue: Database Lock

**Symptoms:**
- Queries hanging
- "Lock timeout" errors

**Diagnosis:**
```bash
# Check for locks
kubectl exec -it postgres-pod -- psql -U AETHER-SCORE -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

**Solutions:**
1. Kill blocking queries
2. Check for long-running transactions
3. Increase lock timeout
4. Optimize migration scripts

## Performance Issues

### Issue: High Memory Usage

**Symptoms:**
- Pods being OOMKilled
- High memory metrics

**Diagnosis:**
```bash
# Check memory usage
kubectl top pods -n AETHER-SCORE-prod

# Check Prometheus metrics
curl http://localhost:8000/metrics | grep memory
```

**Solutions:**
1. Increase memory limits
2. Optimize code (reduce memory allocations)
3. Enable garbage collection tuning
4. Check for memory leaks

### Issue: High CPU Usage

**Symptoms:**
- Slow response times
- High CPU metrics

**Diagnosis:**
```bash
# Check CPU usage
kubectl top pods -n AETHER-SCORE-prod

# Profile application
kubectl exec -it backend-pod -- python -m cProfile -o profile.stats app.py
```

**Solutions:**
1. Scale horizontally
2. Optimize algorithms
3. Enable caching
4. Check for infinite loops
5. Optimize database queries

## Monitoring Issues

### Issue: Metrics Not Appearing

**Symptoms:**
- Prometheus not scraping
- Missing metrics

**Diagnosis:**
```bash
# Check ServiceMonitor
kubectl get servicemonitor -n AETHER-SCORE-prod

# Check metrics endpoint
curl http://localhost:8000/metrics
```

**Solutions:**
1. Verify ServiceMonitor configuration
2. Check Prometheus targets
3. Verify metrics endpoint
4. Check network policies

### Issue: Alerts Not Firing

**Symptoms:**
- Expected alerts not triggering
- Alert rules not working

**Diagnosis:**
```bash
# Check alert rules
kubectl get prometheusrules -n AETHER-SCORE-prod

# Test alert expression
# In Prometheus UI: Test alert expression
```

**Solutions:**
1. Verify alert rule syntax
2. Check alert thresholds
3. Verify Alertmanager configuration
4. Check notification channels



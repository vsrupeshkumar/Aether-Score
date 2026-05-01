# Production Deployment Guide

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker registry access
- PostgreSQL database (managed or self-hosted)
- Redis instance
- QIE testnet/mainnet RPC access
- Domain name with DNS access
- SSL certificate (Let's Encrypt via Cert-Manager)

## Environment Setup

### 1. Create Namespace

```bash
kubectl create namespace AETHER-SCORE-prod
```

### 2. Create Secrets

```bash
# Database credentials
kubectl create secret generic postgres-secret \
  --from-literal=username=AETHER-SCORE \
  --from-literal=password=<secure-password> \
  -n AETHER-SCORE-prod

# Redis password
kubectl create secret generic redis-secret \
  --from-literal=password=<redis-password> \
  -n AETHER-SCORE-prod

# API keys
kubectl create secret generic api-secrets \
  --from-literal=sentry-dsn=<sentry-dsn> \
  --from-literal=jwt-secret=<jwt-secret> \
  -n AETHER-SCORE-prod

# Private keys (encrypted)
kubectl create secret generic blockchain-secrets \
  --from-literal=private-key=<encrypted-private-key> \
  --from-literal=rpc-url=<qie-rpc-url> \
  -n AETHER-SCORE-prod
```

### 3. Create ConfigMap

```bash
kubectl apply -f k8s/base/configmap.yaml -n AETHER-SCORE-prod
```

## Database Setup

### 1. Initialize Database

```bash
# Run migrations
kubectl run alembic-migration \
  --image=AETHER-SCORE/backend:latest \
  --restart=Never \
  --command -- alembic upgrade head \
  -n AETHER-SCORE-prod
```

### 2. Verify Database

```bash
kubectl exec -it <postgres-pod> -n AETHER-SCORE-prod -- psql -U AETHER-SCORE -d AETHER-SCORE
```

## Application Deployment

### 1. Deploy Backend

```bash
# Apply backend deployment
kubectl apply -f k8s/overlays/prod/backend-deployment.yaml -n AETHER-SCORE-prod

# Apply backend service
kubectl apply -f k8s/overlays/prod/backend-service.yaml -n AETHER-SCORE-prod
```

### 2. Deploy Frontend

```bash
# Apply frontend deployment
kubectl apply -f k8s/overlays/prod/frontend-deployment.yaml -n AETHER-SCORE-prod

# Apply frontend service
kubectl apply -f k8s/overlays/prod/frontend-service.yaml -n AETHER-SCORE-prod
```

### 3. Deploy Workers

```bash
# Deploy RQ workers
kubectl apply -f k8s/overlays/prod/worker-deployment.yaml -n AETHER-SCORE-prod
```

### 4. Deploy Ingress

```bash
# Apply ingress configuration
kubectl apply -f k8s/overlays/prod/ingress.yaml -n AETHER-SCORE-prod
```

## SSL Certificate Setup

### 1. Install Cert-Manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### 2. Create ClusterIssuer

```bash
kubectl apply -f k8s/overlays/prod/cluster-issuer.yaml
```

### 3. Verify Certificate

```bash
kubectl get certificate -n AETHER-SCORE-prod
```

## Monitoring Setup

### 1. Deploy Prometheus

```bash
kubectl apply -f k8s/monitoring/prometheus.yaml -n AETHER-SCORE-prod
```

### 2. Deploy Grafana

```bash
kubectl apply -f k8s/monitoring/grafana.yaml -n AETHER-SCORE-prod
```

### 3. Configure Alerts

```bash
kubectl apply -f k8s/monitoring/alert-rules.yaml -n AETHER-SCORE-prod
```

## Verification

### 1. Check Pod Status

```bash
kubectl get pods -n AETHER-SCORE-prod
```

### 2. Check Services

```bash
kubectl get svc -n AETHER-SCORE-prod
```

### 3. Test Health Endpoints

```bash
curl https://api.AETHER-SCORE.io/health
curl https://api.AETHER-SCORE.io/health/ready
```

### 4. Check Logs

```bash
kubectl logs -f deployment/backend -n AETHER-SCORE-prod
kubectl logs -f deployment/frontend -n AETHER-SCORE-prod
```

## Post-Deployment

### 1. Verify Database Connections

```bash
kubectl exec -it deployment/backend -n AETHER-SCORE-prod -- python -c "from database.connection import init_db; import asyncio; asyncio.run(init_db())"
```

### 2. Test API Endpoints

```bash
# Generate test score
curl -X POST https://api.AETHER-SCORE.io/api/score \
  -H "Content-Type: application/json" \
  -d '{"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}'
```

### 3. Monitor Metrics

- Check Prometheus: `https://prometheus.AETHER-SCORE.io`
- Check Grafana: `https://grafana.AETHER-SCORE.io`
- Check Sentry: Monitor error rates

## Rollback Procedure

### 1. Rollback Deployment

```bash
# Rollback backend
kubectl rollout undo deployment/backend -n AETHER-SCORE-prod

# Rollback frontend
kubectl rollout undo deployment/frontend -n AETHER-SCORE-prod
```

### 2. Verify Rollback

```bash
kubectl rollout status deployment/backend -n AETHER-SCORE-prod
kubectl rollout status deployment/frontend -n AETHER-SCORE-prod
```

## Scaling

### 1. Horizontal Scaling

```bash
# Scale backend
kubectl scale deployment/backend --replicas=5 -n AETHER-SCORE-prod

# Scale frontend
kubectl scale deployment/frontend --replicas=3 -n AETHER-SCORE-prod

# Scale workers
kubectl scale deployment/worker --replicas=10 -n AETHER-SCORE-prod
```

### 2. Auto-scaling

```bash
# Apply HPA
kubectl apply -f k8s/overlays/prod/hpa.yaml -n AETHER-SCORE-prod
```

## Backup and Recovery

### 1. Database Backup

```bash
# Manual backup
kubectl exec -it <postgres-pod> -n AETHER-SCORE-prod -- pg_dump -U AETHER-SCORE AETHER-SCORE > backup.sql

# Automated backups (via CronJob)
kubectl apply -f k8s/overlays/prod/backup-cronjob.yaml -n AETHER-SCORE-prod
```

### 2. Restore Database

```bash
kubectl exec -i <postgres-pod> -n AETHER-SCORE-prod -- psql -U AETHER-SCORE AETHER-SCORE < backup.sql
```

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check resource limits and secrets
2. **Database connection errors**: Verify credentials and network policies
3. **High latency**: Check resource usage and scaling
4. **Certificate issues**: Verify Cert-Manager and DNS configuration

### Debug Commands

```bash
# Describe pod
kubectl describe pod <pod-name> -n AETHER-SCORE-prod

# Check events
kubectl get events -n AETHER-SCORE-prod --sort-by='.lastTimestamp'

# Port forward for debugging
kubectl port-forward deployment/backend 8000:8000 -n AETHER-SCORE-prod
```



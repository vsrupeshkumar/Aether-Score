# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm 3.0+ (optional)
- Docker registry access

## Quick Start

### 1. Apply Base Manifests

```bash
kubectl apply -f k8s/base/ -n AETHER-SCORE-prod
```

### 2. Apply Environment Overlay

```bash
kubectl apply -k k8s/overlays/prod/ -n AETHER-SCORE-prod
```

### 3. Verify Deployment

```bash
kubectl get all -n AETHER-SCORE-prod
```

## Manual Deployment

### 1. Create Namespace

```bash
kubectl create namespace AETHER-SCORE-prod
```

### 2. Create Secrets

```bash
# Database
kubectl create secret generic postgres-secret \
  --from-literal=username=AETHER-SCORE \
  --from-literal=password=<password> \
  -n AETHER-SCORE-prod

# Redis
kubectl create secret generic redis-secret \
  --from-literal=password=<password> \
  -n AETHER-SCORE-prod

# API
kubectl create secret generic api-secrets \
  --from-literal=jwt-secret=<secret> \
  --from-literal=sentry-dsn=<dsn> \
  -n AETHER-SCORE-prod
```

### 3. Create ConfigMap

```bash
kubectl apply -f k8s/base/configmap.yaml -n AETHER-SCORE-prod
```

### 4. Deploy Applications

```bash
# Backend
kubectl apply -f k8s/base/backend-deployment.yaml -n AETHER-SCORE-prod
kubectl apply -f k8s/base/backend-service.yaml -n AETHER-SCORE-prod

# Frontend
kubectl apply -f k8s/base/frontend-deployment.yaml -n AETHER-SCORE-prod
kubectl apply -f k8s/base/frontend-service.yaml -n AETHER-SCORE-prod

# Workers
kubectl apply -f k8s/base/worker-deployment.yaml -n AETHER-SCORE-prod
```

### 5. Deploy Ingress

```bash
kubectl apply -f k8s/base/ingress.yaml -n AETHER-SCORE-prod
```

## Using Kustomize

### 1. Base Configuration

```bash
kubectl apply -k k8s/base/
```

### 2. Environment-Specific

```bash
# Development
kubectl apply -k k8s/overlays/dev/

# Staging
kubectl apply -k k8s/overlays/staging/

# Production
kubectl apply -k k8s/overlays/prod/
```

## Resource Management

### Resource Requests and Limits

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Horizontal Pod Autoscaling

```bash
kubectl apply -f k8s/base/hpa.yaml -n AETHER-SCORE-prod
```

## Database Setup

### External Database

If using managed PostgreSQL:

```yaml
# Update ConfigMap with external database URL
DATABASE_URL: postgresql://user:pass@host:5432/AETHER-SCORE
```

### Internal Database (StatefulSet)

```bash
kubectl apply -f k8s/base/postgres-statefulset.yaml -n AETHER-SCORE-prod
```

## Monitoring

### ServiceMonitor (Prometheus)

```bash
kubectl apply -f k8s/monitoring/servicemonitor.yaml -n AETHER-SCORE-prod
```

### Grafana Dashboards

```bash
kubectl apply -f k8s/monitoring/grafana-dashboard.yaml -n AETHER-SCORE-prod
```

## SSL/TLS

### Cert-Manager

```bash
# Install Cert-Manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f k8s/base/cluster-issuer.yaml

# Certificate is automatically created by ingress
```

## Updates and Rollouts

### Rolling Update

```bash
# Update image
kubectl set image deployment/backend backend=AETHER-SCORE/backend:v1.1.0 -n AETHER-SCORE-prod

# Monitor rollout
kubectl rollout status deployment/backend -n AETHER-SCORE-prod
```

### Rollback

```bash
kubectl rollout undo deployment/backend -n AETHER-SCORE-prod
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n AETHER-SCORE-prod
kubectl describe pod <pod-name> -n AETHER-SCORE-prod
```

### View Logs

```bash
kubectl logs -f deployment/backend -n AETHER-SCORE-prod
kubectl logs -f deployment/frontend -n AETHER-SCORE-prod
```

### Debug Container

```bash
kubectl exec -it deployment/backend -n AETHER-SCORE-prod -- bash
```

### Check Events

```bash
kubectl get events -n AETHER-SCORE-prod --sort-by='.lastTimestamp'
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment/backend --replicas=5 -n AETHER-SCORE-prod
```

### Auto-scaling

```bash
# Apply HPA
kubectl apply -f k8s/base/hpa.yaml -n AETHER-SCORE-prod

# Check HPA status
kubectl get hpa -n AETHER-SCORE-prod
```

## Backup and Restore

### Database Backup

```bash
# Create backup job
kubectl apply -f k8s/base/backup-job.yaml -n AETHER-SCORE-prod

# Manual backup
kubectl exec -it <postgres-pod> -n AETHER-SCORE-prod -- \
  pg_dump -U AETHER-SCORE AETHER-SCORE > backup.sql
```

### Restore Database

```bash
kubectl exec -i <postgres-pod> -n AETHER-SCORE-prod -- \
  psql -U AETHER-SCORE AETHER-SCORE < backup.sql
```



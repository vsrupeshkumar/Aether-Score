# Deployment Guide

This guide covers deployment of AETHER-SCORE across different environments, from local development to production.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Quick Start

```bash
# Clone repository
git clone https://github.com/AETHER-SCORE/AETHER-SCORE.git
cd AETHER-SCORE

# Start services with Docker Compose
docker-compose up -d

# Initialize database
docker-compose exec backend alembic upgrade head

# Access services
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Database: localhost:5432
# Redis: localhost:6379
```

### Manual Setup

See [Developer Setup Guide](developer/setup.md) for detailed manual setup instructions.

## Docker Deployment

### Build Images

```bash
# Build backend
cd backend
docker build -t AETHER-SCORE/backend:latest .

# Build frontend
cd frontend
docker build -t AETHER-SCORE/frontend:latest .
```

### Run with Docker Compose

```bash
# Production compose
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/AETHER-SCORE

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Blockchain
QIE_TESTNET_RPC_URL=https://rpc1testnet.qie.digital/
PRIVATE_KEY=<your-private-key>

# Security
JWT_SECRET=<jwt-secret>
API_KEY_ENCRYPTION_KEY=<fernet-key>

# Monitoring
SENTRY_DSN=<sentry-dsn>
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker registry access
- Helm 3+ (optional)

### Quick Start

```bash
# Create namespace
kubectl create namespace AETHER-SCORE-prod

# Apply base configuration
kubectl apply -f k8s/base/ -n AETHER-SCORE-prod

# Apply production overlay
kubectl apply -k k8s/overlays/prod/ -n AETHER-SCORE-prod
```

### Step-by-Step Deployment

#### 1. Create Secrets

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

# API Secrets
kubectl create secret generic api-secrets \
  --from-literal=sentry-dsn=<sentry-dsn> \
  --from-literal=jwt-secret=<jwt-secret> \
  -n AETHER-SCORE-prod

# Blockchain
kubectl create secret generic blockchain-secrets \
  --from-literal=private-key=<private-key> \
  --from-literal=rpc-url=<rpc-url> \
  -n AETHER-SCORE-prod
```

#### 2. Deploy Database

```bash
# If using managed database, skip this step
kubectl apply -f k8s/base/postgres.yaml -n AETHER-SCORE-prod
```

#### 3. Initialize Database

```bash
# Run migrations
kubectl run alembic-migration \
  --image=AETHER-SCORE/backend:latest \
  --restart=Never \
  --command -- alembic upgrade head \
  -n AETHER-SCORE-prod

# Wait for completion
kubectl wait --for=condition=complete job/alembic-migration -n AETHER-SCORE-prod
```

#### 4. Deploy Backend

```bash
# Apply deployment
kubectl apply -f k8s/overlays/prod/backend-deployment.yaml -n AETHER-SCORE-prod

# Apply service
kubectl apply -f k8s/overlays/prod/backend-service.yaml -n AETHER-SCORE-prod

# Wait for rollout
kubectl rollout status deployment/backend -n AETHER-SCORE-prod
```

#### 5. Deploy Frontend

```bash
# Apply deployment
kubectl apply -f k8s/overlays/prod/frontend-deployment.yaml -n AETHER-SCORE-prod

# Apply service
kubectl apply -f k8s/overlays/prod/frontend-service.yaml -n AETHER-SCORE-prod

# Wait for rollout
kubectl rollout status deployment/frontend -n AETHER-SCORE-prod
```

#### 6. Deploy Workers

```bash
# Apply worker deployment
kubectl apply -f k8s/overlays/prod/worker-deployment.yaml -n AETHER-SCORE-prod
```

#### 7. Deploy Ingress

```bash
# Install Cert-Manager (if not installed)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f k8s/overlays/prod/cluster-issuer.yaml

# Apply ingress
kubectl apply -f k8s/overlays/prod/ingress.yaml -n AETHER-SCORE-prod
```

### Verification

```bash
# Check pod status
kubectl get pods -n AETHER-SCORE-prod

# Check services
kubectl get svc -n AETHER-SCORE-prod

# Test health endpoints
curl https://api.AETHER-SCORE.io/health
curl https://api.AETHER-SCORE.io/health/ready

# Check logs
kubectl logs -f deployment/backend -n AETHER-SCORE-prod
```

## Blue-Green Deployment

Blue-green deployment enables zero-downtime deployments by maintaining two identical production environments (blue and green) and switching traffic between them.

### Overview

- **Blue**: Current production environment
- **Green**: New version being deployed
- Traffic is switched from blue to green after successful deployment and health checks
- Automatic rollback if health checks fail

### Prerequisites

- Kubernetes cluster with kubectl access
- Both blue and green deployments configured
- Service with version selector

### Deployment Process

#### 1. Deploy Blue-Green Infrastructure

```bash
# Apply blue-green deployments
kubectl apply -f k8s/overlays/prod/blue-green-deployment.yaml

# Apply service
kubectl apply -f k8s/overlays/prod/blue-green-service.yaml
```

#### 2. Run Blue-Green Deployment

```bash
# Set environment variables
export NAMESPACE=AETHER-SCORE-prod
export IMAGE_TAG=v1.2.0
export DEPLOYMENT_NAME=backend
export SERVICE_NAME=backend

# Run deployment script
./scripts/blue-green-deploy.sh
```

The script will:
1. Deploy new version to inactive environment (green if blue is active)
2. Run health checks
3. Switch traffic to new deployment
4. Monitor for issues
5. Rollback automatically if health checks fail

#### 3. Manual Deployment Steps

If you prefer manual control:

```bash
# 1. Deploy to inactive environment
kubectl set image deployment/backend-green \
  app=AETHER-SCORE-backend:v1.2.0 \
  -n AETHER-SCORE-prod

# 2. Wait for rollout
kubectl rollout status deployment/backend-green -n AETHER-SCORE-prod

# 3. Run health checks
kubectl port-forward deployment/backend-green 4000:4000 -n AETHER-SCORE-prod
curl http://localhost:4000/health

# 4. Switch traffic
kubectl patch svc backend -n AETHER-SCORE-prod \
  -p '{"spec":{"selector":{"version":"green"}}}'

# 5. Verify
kubectl get svc backend -n AETHER-SCORE-prod -o jsonpath='{.spec.selector.version}'
```

### CI/CD Integration

Blue-green deployment is integrated with GitHub Actions:

```bash
# Trigger via GitHub Actions
gh workflow run blue-green-deploy.yml \
  -f environment=production \
  -f image_tag=v1.2.0
```

See `.github/workflows/blue-green-deploy.yml` for full workflow.

### Rollback

If issues are detected after switching traffic:

```bash
# Switch back to previous deployment
./scripts/k8s-rollback.sh backend AETHER-SCORE-prod 1

# Or manually
kubectl patch svc backend -n AETHER-SCORE-prod \
  -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Cleanup

After verifying the new deployment is stable:

```bash
# Scale down old deployment (optional)
kubectl scale deployment/backend-blue --replicas=0 -n AETHER-SCORE-prod
```

### Best Practices

- Always run health checks before switching traffic
- Monitor metrics for 5-10 minutes after switch
- Keep old deployment running for quick rollback
- Use staging environment to test blue-green process
- Document any manual steps taken

## SSL Certificate Management

Automated SSL certificate management using Cert-Manager and Let's Encrypt.

### Overview

- Automatic certificate issuance and renewal
- Let's Encrypt integration (free SSL certificates)
- HTTP-01 challenge validation
- Automatic renewal 30 days before expiration

### Prerequisites

- Kubernetes cluster with admin access
- kubectl configured
- Ingress controller (nginx-ingress) installed
- DNS records pointing to ingress IP
- Cert-Manager installed

### Installation

#### 1. Install Cert-Manager

```bash
# Using installation script
./k8s/cert-manager/install.sh

# Or manually with Helm
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

#### 2. Verify Installation

```bash
# Check pods
kubectl get pods -n cert-manager

# All pods should be Running
```

### Configuration

#### 1. Create ClusterIssuer

The ClusterIssuer defines how certificates are obtained:

```bash
# Update email in cluster-issuer.yaml first
kubectl apply -f k8s/overlays/prod/cluster-issuer.yaml
```

**Important:** Update the email address in `cluster-issuer.yaml` before applying.

#### 2. Create Certificate Resource

Define which domains need certificates:

```bash
kubectl apply -f k8s/overlays/prod/certificate.yaml
```

#### 3. Verify Ingress Configuration

Ensure your Ingress has the cert-manager annotation:

```yaml
annotations:
  cert-manager.io/cluster-issuer: letsencrypt-prod
```

This is already configured in `k8s/base/ingress.yaml`.

### Verification

#### Check Certificate Status

```bash
# List certificates
kubectl get certificate -n AETHER-SCORE-prod

# Describe certificate
kubectl describe certificate AETHER-SCORE-tls -n AETHER-SCORE-prod
```

Status should be `Ready` once issued.

#### Check Certificate Secret

```bash
# Verify secret was created
kubectl get secret AETHER-SCORE-tls -n AETHER-SCORE-prod

# View certificate details
kubectl get secret AETHER-SCORE-tls -n AETHER-SCORE-prod -o yaml
```

#### Test HTTPS

```bash
# Test endpoint
curl -I https://api.AETHER-SCORE.io/health

# Should return 200 with valid SSL certificate
```

### Troubleshooting

#### Certificate Not Issuing

1. Check certificate status:
   ```bash
   kubectl describe certificate AETHER-SCORE-tls -n AETHER-SCORE-prod
   ```

2. Check certificate request:
   ```bash
   kubectl get certificaterequest -n AETHER-SCORE-prod
   kubectl describe certificaterequest <name> -n AETHER-SCORE-prod
   ```

3. Check challenge status:
   ```bash
   kubectl get challenge -n AETHER-SCORE-prod
   kubectl describe challenge <name> -n AETHER-SCORE-prod
   ```

4. Check cert-manager logs:
   ```bash
   kubectl logs -f deployment/cert-manager -n cert-manager
   ```

#### Common Issues

- **DNS not configured**: Ensure DNS A records point to ingress IP
- **Ingress not accessible**: Verify ingress controller is running
- **Rate limiting**: Let's Encrypt has rate limits (50 certs/week/domain)
- **Email not set**: Update email in ClusterIssuer
- **HTTP-01 challenge failing**: Ensure ingress is publicly accessible

### Auto-Renewal

Cert-manager automatically renews certificates:
- Renewal starts 30 days before expiration
- No manual intervention required
- Renewal process is transparent

### Staging vs Production

Use staging issuer for testing:

```yaml
# In certificate.yaml
spec:
  issuerRef:
    name: letsencrypt-staging  # Use staging for testing
    kind: ClusterIssuer
```

Switch to production issuer when ready:

```yaml
spec:
  issuerRef:
    name: letsencrypt-prod  # Use production
    kind: ClusterIssuer
```

### Additional Resources

- [Cert-Manager Documentation](https://cert-manager.io/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Installation Guide](k8s/cert-manager/README.md)

## Environment Configuration

### Development

```bash
# .env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql+asyncpg://localhost:5432/AETHER-SCORE_dev
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Staging

```bash
# .env
ENVIRONMENT=staging
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://staging-db:5432/AETHER-SCORE_staging
REDIS_HOST=staging-redis
REDIS_PORT=6379
SENTRY_DSN=<staging-sentry-dsn>
```

### Production

```bash
# .env
ENVIRONMENT=production
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://prod-db:5432/AETHER-SCORE_prod
REDIS_HOST=prod-redis
REDIS_PORT=6379
SENTRY_DSN=<prod-sentry-dsn>
```

## Rollback Procedures

### Docker Compose

```bash
# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --scale backend=0
# Update images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

#### Quick Rollback

```bash
# Rollback backend to previous revision
kubectl rollout undo deployment/backend -n AETHER-SCORE-prod

# Rollback frontend
kubectl rollout undo deployment/frontend -n AETHER-SCORE-prod

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n AETHER-SCORE-prod

# Verify rollback
kubectl rollout status deployment/backend -n AETHER-SCORE-prod
```

#### Using Rollback Scripts

```bash
# Rollback single service
./scripts/k8s-rollback.sh AETHER-SCORE-prod backend

# Rollback to specific revision
./scripts/k8s-rollback.sh AETHER-SCORE-prod backend 3

# Rollback all services
./scripts/rollback-all.sh AETHER-SCORE-prod

# Rollback all to specific revision
./scripts/rollback-all.sh AETHER-SCORE-prod 2
```

#### View Rollout History

```bash
# View history for a deployment
kubectl rollout history deployment/backend -n AETHER-SCORE-prod

# View details of a specific revision
kubectl rollout history deployment/backend --revision=3 -n AETHER-SCORE-prod
```

#### Rollback via GitHub Actions

1. Go to Actions â†’ Rollback Deployment
2. Click "Run workflow"
3. Select environment (dev/staging/prod)
4. Optionally specify deployment and revision
5. Click "Run workflow"

### Database Rollback

#### Migration Rollback

```bash
# Rollback last migration
kubectl run alembic-rollback \
  --image=AETHER-SCORE/backend:latest \
  --restart=Never \
  --command -- alembic downgrade -1 \
  -n AETHER-SCORE-prod

# Rollback multiple migrations
kubectl run alembic-rollback \
  --image=AETHER-SCORE/backend:latest \
  --restart=Never \
  --command -- alembic downgrade -3 \
  -n AETHER-SCORE-prod

# Or use the rollback script
./scripts/rollback-migration.sh production 1
```

#### Database Restore (Full Rollback)

See [Backup & Recovery](#backup--recovery) section for complete database restore procedures.

### Rollback Verification

After rollback, verify:

1. **Service Health**
   ```bash
   curl https://api.AETHER-SCORE.io/health
   curl https://api.AETHER-SCORE.io/health/ready
   ```

2. **Deployment Status**
   ```bash
   kubectl get deployments -n AETHER-SCORE-prod
   kubectl get pods -n AETHER-SCORE-prod
   ```

3. **Application Functionality**
   ```bash
   # Test API endpoint
   curl -X POST https://api.AETHER-SCORE.io/api/score \
     -H "X-API-Key: test-key" \
     -H "Content-Type: application/json" \
     -d '{"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"}'
   ```

4. **Check Logs**
   ```bash
   kubectl logs -f deployment/backend -n AETHER-SCORE-prod --tail=100
   ```

## Scaling

### Horizontal Scaling

```bash
# Kubernetes
kubectl scale deployment/backend --replicas=5 -n AETHER-SCORE-prod
kubectl scale deployment/frontend --replicas=3 -n AETHER-SCORE-prod
kubectl scale deployment/worker --replicas=10 -n AETHER-SCORE-prod

# Docker Compose
docker-compose -f docker-compose.prod.yml up -d --scale backend=5 --scale worker=10
```

### Auto-Scaling

```bash
# Apply HPA
kubectl apply -f k8s/overlays/prod/hpa.yaml -n AETHER-SCORE-prod

# Check HPA status
kubectl get hpa -n AETHER-SCORE-prod
```

## Monitoring

### Health Checks

```bash
# Liveness
curl https://api.AETHER-SCORE.io/health

# Readiness
curl https://api.AETHER-SCORE.io/health/ready

# Metrics
curl https://api.AETHER-SCORE.io/metrics
```

### Logs

```bash
# Kubernetes
kubectl logs -f deployment/backend -n AETHER-SCORE-prod
kubectl logs -f deployment/frontend -n AETHER-SCORE-prod

# Docker Compose
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Metrics

- **Prometheus**: `https://prometheus.AETHER-SCORE.io`
- **Grafana**: `https://grafana.AETHER-SCORE.io`
- **Sentry**: Monitor error rates

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n AETHER-SCORE-prod

# Check events
kubectl get events -n AETHER-SCORE-prod --sort-by='.lastTimestamp'

# Check resource limits
kubectl top pod <pod-name> -n AETHER-SCORE-prod
```

#### Database Connection Errors

```bash
# Verify database is running
kubectl get pods -l app=postgres -n AETHER-SCORE-prod

# Check database credentials
kubectl get secret postgres-secret -n AETHER-SCORE-prod -o yaml

# Test connection
kubectl run db-test \
  --image=postgres:15 \
  --restart=Never \
  --rm -it \
  -- psql -h postgres -U AETHER-SCORE -d AETHER-SCORE
```

#### High Latency

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n AETHER-SCORE-prod

# Check network policies
kubectl get networkpolicies -n AETHER-SCORE-prod

# Check service endpoints
kubectl get endpoints -n AETHER-SCORE-prod
```

#### Certificate Issues

```bash
# Check certificate status
kubectl get certificate -n AETHER-SCORE-prod

# Check cert-manager logs
kubectl logs -f deployment/cert-manager -n cert-manager

# Verify DNS
dig api.AETHER-SCORE.io
```

### Debug Commands

```bash
# Port forward for local debugging
kubectl port-forward deployment/backend 8000:8000 -n AETHER-SCORE-prod
kubectl port-forward deployment/frontend 3000:3000 -n AETHER-SCORE-prod

# Execute command in pod
kubectl exec -it deployment/backend -n AETHER-SCORE-prod -- /bin/bash

# View pod logs
kubectl logs -f deployment/backend -n AETHER-SCORE-prod --tail=100
```

## Backup and Recovery

### Database Backup

```bash
# Manual backup
kubectl exec -it <postgres-pod> -n AETHER-SCORE-prod -- \
  pg_dump -U AETHER-SCORE AETHER-SCORE > backup-$(date +%Y%m%d).sql

# Automated backups (CronJob)
kubectl apply -f k8s/overlays/prod/backup-cronjob.yaml -n AETHER-SCORE-prod
```

### Database Restore

```bash
# Restore from backup
kubectl exec -i <postgres-pod> -n AETHER-SCORE-prod -- \
  psql -U AETHER-SCORE AETHER-SCORE < backup-20240101.sql
```

## CI/CD Integration

### GitHub Actions

Deployments are automated via GitHub Actions:

```yaml
# .github/workflows/deploy-prod.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/backend \
            backend=AETHER-SCORE/backend:${{ github.sha }} \
            -n AETHER-SCORE-prod
```

## Support

- **Documentation**: https://docs.AETHER-SCORE.io/deployment
- **GitHub Issues**: https://github.com/AETHER-SCORE/AETHER-SCORE/issues
- **Email**: devops@AETHER-SCORE.io



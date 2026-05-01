# Environment Variables Setup

## Overview

This document lists all environment variables required for AETHER-SCORE deployment.

## Backend Environment Variables

### Database

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/AETHER-SCORE
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
```

### Redis

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

### Blockchain

```bash
QIE_TESTNET_RPC_URL=https://rpc1testnet.qie.digital/
QIE_MAINNET_RPC_URL=https://rpc1.qie.digital/
QIE_CHAIN_ID=12345
PRIVATE_KEY=<encrypted-private-key>
CREDIT_PASSPORT_NFT_ADDRESS=0x...
STAKING_CONTRACT_ADDRESS=0x...
LENDING_VAULT_ADDRESS=0x...
```

### Authentication

```bash
JWT_SECRET=<random-secret-key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
API_KEY_ENCRYPTION_KEY=<fernet-key>
```

### Security

```bash
ALLOWED_ORIGINS=http://localhost:3000,https://AETHER-SCORE.io
CORS_ENABLED=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

### Monitoring

```bash
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
PROMETHEUS_ENABLED=true
```

### Application

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
APP_VERSION=1.0.0
```

## Frontend Environment Variables

### API

```bash
NEXT_PUBLIC_API_URL=https://api.AETHER-SCORE.io
NEXT_PUBLIC_CHAIN_ID=12345
NEXT_PUBLIC_RPC_URL=https://rpc1testnet.qie.digital/
```

### Contracts

```bash
NEXT_PUBLIC_CREDIT_PASSPORT_NFT_ADDRESS=0x...
NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=0x...
NEXT_PUBLIC_LENDING_VAULT_ADDRESS=0x...
```

### Monitoring

```bash
NEXT_PUBLIC_SENTRY_DSN=https://...
NEXT_PUBLIC_SENTRY_ENVIRONMENT=production
```

## Environment-Specific Configurations

### Development

```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql+asyncpg://localhost:5432/AETHER-SCORE_dev
REDIS_HOST=localhost
```

### Staging

```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://staging-db:5432/AETHER-SCORE_staging
SENTRY_ENVIRONMENT=staging
```

### Production

```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://prod-db:5432/AETHER-SCORE
SENTRY_ENVIRONMENT=production
RATE_LIMIT_PER_MINUTE=30
```

## Secrets Management

### Using Kubernetes Secrets

```bash
# Create secret
kubectl create secret generic AETHER-SCORE-secrets \
  --from-literal=database-url=<url> \
  --from-literal=jwt-secret=<secret> \
  -n AETHER-SCORE-prod
```

### Using Environment Files

```bash
# .env file (never commit)
DATABASE_URL=...
JWT_SECRET=...
PRIVATE_KEY=...
```

## Validation

### Backend Validation

The backend validates all required environment variables on startup:

```python
# Required variables
REQUIRED_VARS = [
    "DATABASE_URL",
    "REDIS_HOST",
    "JWT_SECRET",
    "QIE_TESTNET_RPC_URL",
]
```

### Frontend Validation

Next.js validates public environment variables at build time.

## Security Best Practices

1. **Never commit secrets**: Use `.env.example` for templates
2. **Encrypt sensitive data**: Use Fernet encryption for private keys
3. **Rotate secrets regularly**: Update JWT secrets and API keys
4. **Use secret management**: Kubernetes Secrets, AWS Secrets Manager, etc.
5. **Limit access**: Only grant access to necessary environment variables



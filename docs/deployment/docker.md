# Docker Deployment Guide

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- 20GB+ disk space

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/AETHER-SCORE.git
cd AETHER-SCORE
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Initialize Database

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Verify Deployment

```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Test API
curl http://localhost:8000/health
```

## Production Deployment

### 1. Build Images

```bash
# Build backend
docker build -t AETHER-SCORE/backend:latest -f backend/Dockerfile .

# Build frontend
docker build -t AETHER-SCORE/frontend:latest -f frontend/Dockerfile .
```

### 2. Tag and Push

```bash
docker tag AETHER-SCORE/backend:latest registry.example.com/AETHER-SCORE/backend:v1.0.0
docker tag AETHER-SCORE/frontend:latest registry.example.com/AETHER-SCORE/frontend:v1.0.0

docker push registry.example.com/AETHER-SCORE/backend:v1.0.0
docker push registry.example.com/AETHER-SCORE/frontend:v1.0.0
```

### 3. Deploy with Docker Compose

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

## Service Configuration

### Backend Service

- **Port**: 8000
- **Health Check**: `/health`
- **Environment Variables**: See `.env.example`

### Frontend Service

- **Port**: 3000
- **Build**: Next.js standalone
- **Environment Variables**: `NEXT_PUBLIC_API_URL`

### Database Service

- **Port**: 5432
- **Database**: `AETHER-SCORE`
- **User**: `AETHER-SCORE`

### Redis Service

- **Port**: 6379
- **Persistent Volume**: `/data`

## Volume Management

### Persistent Volumes

```yaml
volumes:
  postgres_data:
  redis_data:
  backend_logs:
```

### Backup Volumes

```bash
# Backup database
docker run --rm -v AETHER-SCORE_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore database
docker run --rm -v AETHER-SCORE_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

## Networking

### Default Network

All services are on the `AETHER-SCORE_default` network.

### External Access

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Database**: `localhost:5432` (internal only)
- **Redis**: `localhost:6379` (internal only)

## Scaling

### Scale Services

```bash
# Scale backend
docker-compose up -d --scale backend=3

# Scale workers
docker-compose up -d --scale worker=5
```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Resource Usage

```bash
docker stats
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in `docker-compose.yml`
2. **Out of memory**: Increase Docker memory limit
3. **Database connection**: Check network and credentials
4. **Build failures**: Clear Docker cache

### Debug Commands

```bash
# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

# Inspect container
docker-compose exec backend python -c "import sys; print(sys.path)"

# Check network
docker network inspect AETHER-SCORE_default
```

## Cleanup

### Stop Services

```bash
docker-compose down
```

### Remove Volumes

```bash
docker-compose down -v
```

### Remove Images

```bash
docker-compose down --rmi all
```



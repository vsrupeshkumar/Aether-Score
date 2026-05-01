# Monitoring & Observability Guide

## Overview

AETHER-SCORE implements comprehensive monitoring and observability using Sentry (error tracking + APM), Prometheus (metrics), structured logging, and blockchain monitoring.

## Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  AETHER-SCORE  â”‚
â”‚ Application â”‚
â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
       â”‚
       â”œâ”€â”€â”€ Sentry (Errors + Performance)
       â”œâ”€â”€â”€ Prometheus (Metrics)
       â”œâ”€â”€â”€ Structured Logs (JSON)
       â””â”€â”€â”€ Blockchain Monitor
```

## Components

### 1. Sentry Integration

**Backend:**
- Error tracking with stack traces
- Performance monitoring (APM)
- Release tracking
- Custom tags and context

**Frontend:**
- Client-side error tracking
- Session replay (privacy-compliant)
- Performance monitoring
- Error boundaries

**Configuration:**
```bash
SENTRY_DSN_BACKEND=https://xxx@sentry.io/xxx
SENTRY_DSN_FRONTEND=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 2. Prometheus Metrics

**Endpoint:** `/metrics`

**Key Metrics:**
- HTTP request metrics (count, duration, status codes)
- API endpoint metrics
- Blockchain transaction metrics
- Score computation metrics
- Oracle call metrics
- Error rates

**Access:**
```bash
curl http://localhost:8000/metrics
```

### 3. Structured Logging

**Format:** JSON

**Log Levels:**
- DEBUG: Detailed debugging information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

**Configuration:**
```bash
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**Features:**
- Correlation IDs for request tracing
- Anonymized user addresses
- Structured JSON format
- Log rotation (10MB files, 5 backups)

### 4. Health Checks

**Endpoints:**
- `/health` - Liveness check (always returns healthy if app is running)
- `/health/ready` - Readiness check (validates dependencies)

**Dependencies Checked:**
- Blockchain RPC connectivity
- Redis connectivity (if configured)
- Oracle service availability

### 5. Blockchain Monitoring

**Monitors:**
- Contract events (PassportMinted, ScoreUpdated, etc.)
- Transaction status and confirmation times
- Failed transactions with revert reasons
- Gas usage patterns

**Configuration:**
```bash
BLOCKCHAIN_MONITORING_ENABLED=true
```

### 6. Performance Monitoring

**Tracks:**
- Slow requests (>1s, >5s thresholds)
- API response times
- External API latencies
- Score computation duration

**Alerts:**
- Very slow requests (>5s) â†’ Sentry warning
- Slow requests (>1s) â†’ Logged

## Setup

### 1. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create `.env` file with:

```bash
# Sentry
SENTRY_DSN_BACKEND=https://xxx@sentry.io/xxx
SENTRY_DSN_FRONTEND=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=1.0.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Metrics
METRICS_ENABLED=true

# Monitoring
MONITORING_ENABLED=true
PERFORMANCE_MONITORING_ENABLED=true
BLOCKCHAIN_MONITORING_ENABLED=true
```

### 3. Start Services

**Backend:**
```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Monitoring Dashboards

### Sentry Dashboard

1. Go to https://sentry.io
2. Navigate to your project
3. View:
   - Issues (errors)
   - Performance (APM)
   - Releases
   - Alerts

### Grafana Dashboard

1. Import dashboard from `grafana/dashboards/AETHER-SCORE.json`
2. Configure Prometheus data source
3. View metrics and create custom panels

### Prometheus

1. Configure scrape config:
```yaml
scrape_configs:
  - job_name: 'AETHER-SCORE'
    static_configs:
      - targets: ['localhost:8000']
```

2. Access Prometheus UI: http://localhost:9090

## Alerting

See [ALERTING.md](ALERTING.md) for detailed alert configuration.

### Key Alerts

- High error rate (>10 errors/min)
- Slow response times (P95 > 2s)
- Service downtime
- Blockchain RPC failures
- High transaction failure rate

## Best Practices

1. **Monitor Key Metrics**: Focus on error rates, latency, and availability
2. **Set Appropriate Thresholds**: Avoid alert fatigue
3. **Regular Review**: Review metrics and alerts weekly
4. **Documentation**: Keep runbooks for common issues
5. **Testing**: Test alerting regularly

## Troubleshooting

### Metrics Not Appearing

1. Check `METRICS_ENABLED=true` in environment
2. Verify `/metrics` endpoint is accessible
3. Check Prometheus scrape configuration

### Sentry Not Capturing Errors

1. Verify DSN is correct
2. Check environment variables
3. Verify Sentry initialization in `app.py`

### Logs Not Structured

1. Check `LOG_LEVEL` environment variable
2. Verify logger setup in `utils/logger.py`
3. Check log file permissions

## Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [METRICS.md](METRICS.md) - Available metrics
- [ALERTING.md](ALERTING.md) - Alert configuration



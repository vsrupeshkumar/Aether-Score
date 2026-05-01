# Alerting Configuration Guide

## Overview

AETHER-SCORE uses Sentry and Prometheus for alerting on critical issues, performance degradation, and system failures.

## Sentry Alerts

### Configuration

Sentry alerts are configured in the Sentry dashboard. Navigate to:
- **Alerts** â†’ **Create Alert Rule**

### Recommended Alert Rules

#### 1. Critical Errors
- **Trigger**: When an issue is seen more than 5 times in 1 minute
- **Action**: Send email/Slack notification
- **Filters**: 
  - Level: Error or Fatal
  - Tags: `service=AETHER-SCORE-backend` or `service=AETHER-SCORE-frontend`

#### 2. High Error Rate
- **Trigger**: When error rate exceeds 10 errors/minute
- **Action**: Send email/Slack notification
- **Window**: 5 minutes

#### 3. Performance Degradation
- **Trigger**: When P95 latency exceeds 2 seconds
- **Action**: Send email notification
- **Window**: 10 minutes

#### 4. Failed Blockchain Transactions
- **Trigger**: When transaction failure rate > 10%
- **Action**: Send Slack notification
- **Filters**: 
  - Tags: `operation=blockchain_transaction`
  - Message contains: "transaction failed"

#### 5. Service Unavailable
- **Trigger**: When health check endpoint returns 503
- **Action**: Page on-call engineer
- **Window**: 2 minutes

### Alert Channels

Configure in Sentry:
1. **Email**: Default channel for all alerts
2. **Slack**: For critical alerts
3. **PagerDuty/Opsgenie**: For on-call escalation

## Prometheus Alerts

### Configuration

Prometheus alerts are defined in `prometheus/alerts.yml` and loaded by Prometheus server.

### Alert Rules

#### High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(errors_total[5m]) > 10
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
```

#### Slow Response Time
```yaml
- alert: SlowResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: warning
```

#### Service Down
```yaml
- alert: ServiceDown
  expr: up{job="AETHER-SCORE"} == 0
  for: 1m
  labels:
    severity: critical
```

#### Blockchain RPC Failures
```yaml
- alert: BlockchainRPCFailures
  expr: rate(blockchain_rpc_errors_total[5m]) > 5
  for: 5m
  labels:
    severity: warning
```

### Alertmanager Configuration

Configure Alertmanager to route alerts:

```yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@AETHER-SCORE.io'
  
  - name: 'critical-alerts'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#alerts-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
  
  - name: 'warning-alerts'
    email_configs:
      - to: 'team@AETHER-SCORE.io'
```

## Alert Thresholds

### Error Rates
- **Warning**: > 5 errors/minute
- **Critical**: > 10 errors/minute

### Response Times
- **Warning**: P95 > 1 second
- **Critical**: P95 > 2 seconds

### Blockchain
- **Warning**: > 5 RPC errors/minute
- **Critical**: > 10% transaction failure rate

### Service Health
- **Critical**: Service down for > 1 minute
- **Warning**: Dependencies unhealthy for > 5 minutes

## Testing Alerts

### Test Sentry Alert
```python
from utils.monitoring import capture_message
capture_message("Test alert", level="error")
```

### Test Prometheus Alert
```bash
# Manually trigger metric
curl -X POST http://localhost:8000/api/score \
  -H "Content-Type: application/json" \
  -d '{"address": "invalid"}'
```

## Best Practices

1. **Avoid Alert Fatigue**: Set appropriate thresholds
2. **Group Related Alerts**: Use alert grouping in Alertmanager
3. **Escalation Policies**: Define clear escalation paths
4. **Runbooks**: Document response procedures for each alert
5. **Regular Review**: Review and adjust thresholds monthly

## Integration with Monitoring Tools

- **Sentry**: Error tracking and performance monitoring
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and alerting
- **Alertmanager**: Alert routing and notification

## Environment Variables

```bash
# Sentry
SENTRY_DSN_BACKEND=https://xxx@sentry.io/xxx
SENTRY_DSN_FRONTEND=https://xxx@sentry.io/xxx

# Alert Webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
PAGERDUTY_SERVICE_KEY=xxx
```



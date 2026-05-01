# Uptime Monitoring Setup Guide

## Overview

External uptime monitoring ensures AETHER-SCORE is available and responding correctly. This guide covers setup for UptimeRobot and Pingdom.

## Health Check Endpoints

### Liveness Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "AETHER-SCORE API",
  "version": "1.0.0",
  "environment": "production"
}
```

**Use Case:** Basic health check - returns healthy if application is running.

### Readiness Check
```
GET /health/ready
```

**Response:**
```json
{
  "status": "ready",
  "service": "AETHER-SCORE API",
  "version": "1.0.0",
  "dependencies": {
    "blockchain": {
      "status": "healthy",
      "connected": true,
      "latest_block": 12345
    },
    "redis": {
      "status": "healthy",
      "connected": true
    },
    "oracle": {
      "status": "healthy",
      "price_available": true
    }
  }
}
```

**Use Case:** Full readiness check - validates all dependencies.

## UptimeRobot Setup

### 1. Create Account
1. Go to https://uptimerobot.com
2. Sign up for free account
3. Verify email

### 2. Add Monitor

**Monitor Type:** HTTP(s)

**Settings:**
- **Friendly Name:** AETHER-SCORE API
- **URL:** `https://your-api-domain.com/health`
- **Monitoring Interval:** 5 minutes
- **Timeout:** 30 seconds
- **Alert Contacts:** Add email/SMS

**Advanced Settings:**
- **Keyword:** `"status":"healthy"` (to verify response content)
- **Alert When:** Down for 2 consecutive checks

### 3. Readiness Monitor (Optional)

Create a second monitor for `/health/ready`:
- **URL:** `https://your-api-domain.com/health/ready`
- **Keyword:** `"status":"ready"`
- **Alert When:** Down for 1 check (more sensitive)

### 4. Alert Configuration

**Alert Contacts:**
- Email: team@AETHER-SCORE.io
- SMS: +1-XXX-XXX-XXXX (for critical alerts)
- Webhook: Slack/Discord webhook URL

**Alert Thresholds:**
- **Warning:** 1 failed check
- **Critical:** 3 consecutive failed checks

## Pingdom Setup

### 1. Create Account
1. Go to https://www.pingdom.com
2. Sign up for account
3. Choose plan (free tier available)

### 2. Add Check

**Check Type:** HTTP

**Settings:**
- **Name:** AETHER-SCORE API Health
- **URL:** `https://your-api-domain.com/health`
- **Check Interval:** 1 minute
- **Timeout:** 10 seconds

**Advanced:**
- **Expected Status Code:** 200
- **Expected Response Body:** `"status":"healthy"`
- **Follow Redirects:** Yes

### 3. Alert Configuration

**Notification Channels:**
- Email
- SMS
- Push notifications
- Webhooks (Slack, PagerDuty)

**Alert Rules:**
- **Immediate:** Service down
- **Escalation:** Down for > 5 minutes

## Example Configurations

### UptimeRobot JSON

```json
{
  "monitor": {
    "friendly_name": "AETHER-SCORE API",
    "url": "https://api.AETHER-SCORE.io/health",
    "type": 1,
    "interval": 300,
    "timeout": 30,
    "keyword_type": 1,
    "keyword_value": "healthy",
    "alert_contacts": ["email_12345"]
  }
}
```

### Pingdom Check

```yaml
name: AETHER-SCORE API Health
type: http
url: https://api.AETHER-SCORE.io/health
interval: 60
timeout: 10
expected_status: 200
expected_body: "status":"healthy"
notifications:
  - email: team@AETHER-SCORE.io
  - slack: https://hooks.slack.com/...
```

## Monitoring Best Practices

### 1. Multiple Endpoints
- Monitor both `/health` and `/health/ready`
- Use different alert thresholds

### 2. Geographic Distribution
- Monitor from multiple locations
- Detect regional issues

### 3. Alert Thresholds
- **Liveness:** Alert after 2 failed checks (10 minutes)
- **Readiness:** Alert after 1 failed check (5 minutes)

### 4. Maintenance Windows
- Schedule maintenance windows
- Pause monitoring during planned downtime

### 5. Status Page
- Create public status page
- Update during incidents
- Link from main website

## Integration with Other Tools

### Status Page Services
- **Statuspage.io**: Public status page
- **Cachet**: Open-source status page
- **UptimeRobot Status Page**: Built-in status page

### Incident Management
- **PagerDuty**: On-call management
- **Opsgenie**: Alert management
- **VictorOps**: Incident response

## Testing

### Test Health Endpoints

```bash
# Liveness
curl https://api.AETHER-SCORE.io/health

# Readiness
curl https://api.AETHER-SCORE.io/health/ready
```

### Simulate Downtime

1. Stop backend service
2. Verify monitor detects downtime
3. Check alert delivery
4. Restart service
5. Verify recovery alert

## Alert Response Procedures

### When Alert Fires

1. **Check Status:**
   - Visit `/health/ready` endpoint
   - Check Sentry for errors
   - Review recent deployments

2. **Investigate:**
   - Check application logs
   - Review dependency status
   - Check blockchain RPC status

3. **Communicate:**
   - Update status page
   - Notify team via Slack
   - Document incident

4. **Resolve:**
   - Fix underlying issue
   - Verify recovery
   - Post-mortem review

## Cost Considerations

### Free Tiers
- **UptimeRobot**: 50 monitors, 5-minute intervals (free)
- **Pingdom**: 1 check, 1-minute interval (free trial)

### Paid Options
- **UptimeRobot Pro**: $7/month (1-minute intervals)
- **Pingdom**: $10/month (1 check, 1-minute interval)

## Recommended Setup

### Production
- **Primary:** UptimeRobot (free tier, 5-minute checks)
- **Secondary:** Pingdom (1-minute checks for critical)
- **Status Page:** UptimeRobot Status Page (free)

### Development/Staging
- **UptimeRobot:** 1 monitor (free tier sufficient)

## Environment Variables

No additional environment variables needed for external monitoring. Health endpoints are public and don't require authentication.

## Security Considerations

1. **Rate Limiting:** Health endpoints are exempt from rate limiting
2. **No Authentication:** Health checks don't require auth
3. **Minimal Data:** Health endpoints return minimal information
4. **IP Whitelisting:** Optional - whitelist monitor IPs if needed

## Troubleshooting

### Monitor Shows Down But Service Is Up

1. Check firewall rules
2. Verify DNS resolution
3. Check SSL certificate validity
4. Review rate limiting rules

### False Positives

1. Adjust alert thresholds
2. Increase check interval
3. Add keyword verification
4. Review timeout settings

## Next Steps

1. Set up UptimeRobot account
2. Configure monitors for `/health` and `/health/ready`
3. Set up alert contacts
4. Test alert delivery
5. Create status page
6. Document incident response procedures



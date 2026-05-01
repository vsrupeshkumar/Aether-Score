# Analytics & Privacy Policy

## Overview

AETHER-SCORE implements privacy-compliant analytics using Sentry and custom tracking. All user data is anonymized and no personally identifiable information (PII) is stored.

## Privacy Principles

1. **Anonymization**: All wallet addresses are anonymized (first 8 + last 4 chars)
2. **Hashing**: Consistent but anonymous user IDs via SHA256 hashing
3. **No PII**: No names, emails, or other personal information collected
4. **Opt-out**: Users can disable analytics via browser settings

## What We Track

### Feature Usage
- Score generation requests
- Loan creation attempts
- Staking operations
- Chat interactions

### User Flows
- Wallet connect â†’ Score generation â†’ Loan creation
- Feature discovery patterns
- Error recovery paths

### Performance Metrics
- API response times (anonymized by endpoint)
- Error rates by user segment (not by individual)
- Geographic performance (country-level, not precise location)

### Error Analytics
- Error types and frequencies
- Error rates by user segment
- Performance issues by location (anonymized)

## What We DON'T Track

- Full wallet addresses
- Transaction details
- Personal information
- Precise geographic location
- IP addresses (only country-level)

## Implementation

### Backend Analytics

```python
from utils.analytics import track_feature_usage, track_user_flow

# Track feature usage
track_feature_usage("score_generation", address=user_address)

# Track user flow
track_user_flow("score_generated", "score_to_loan", address=user_address)
```

### Frontend Analytics

Sentry automatically tracks:
- Page views (anonymized)
- User interactions (anonymized)
- Error occurrences
- Performance metrics

## Data Retention

- **Sentry**: 90 days (configurable)
- **Prometheus**: 30 days (configurable)
- **Logs**: 7 days (configurable)

## User Rights

Users have the right to:
1. **Access**: Request what data is collected (anonymized)
2. **Delete**: Request deletion of analytics data
3. **Opt-out**: Disable analytics via browser settings

## Compliance

- **GDPR**: Compliant (no PII, anonymized data)
- **CCPA**: Compliant (anonymized, opt-out available)
- **Privacy by Design**: Built into architecture

## Configuration

Analytics can be disabled via environment variables:

```bash
# Disable Sentry
SENTRY_DSN_BACKEND=""
SENTRY_DSN_FRONTEND=""

# Disable analytics tracking
ANALYTICS_ENABLED=false
```

## Contact

For privacy concerns or data requests, contact: privacy@AETHER-SCORE.io



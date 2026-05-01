# Security Implementation Guide

## Overview

AETHER-SCORE backend implements comprehensive security features including authentication, rate limiting, input validation, encrypted secrets management, and audit logging.

## Authentication

### API Keys

API keys are configured via the `API_KEYS` environment variable (comma-separated list).

**Usage:**
```bash
curl -H "Authorization: ApiKey your-api-key" https://api.AETHER-SCORE.com/api/score
```

### JWT Tokens

JWT tokens are issued via `/api/auth/token` endpoint using wallet signature verification.

**Get Token:**
```bash
POST /api/auth/token
{
  "address": "0x...",
  "signature": "0x...",
  "message": "AETHER-SCORE Authentication\n..."
}
```

**Use Token:**
```bash
curl -H "Authorization: Bearer <jwt-token>" https://api.AETHER-SCORE.com/api/score
```

### Wallet Signature

For wallet-based authentication, include signature in request:

```json
{
  "address": "0x...",
  "signature": "0x...",
  "message": "...",
  "timestamp": 1234567890
}
```

## Rate Limiting

- **Per IP**: 60 requests/minute, 1000 requests/hour
- **Per User** (authenticated): 1000 requests/hour
- **Score Generation**: 10 requests/minute
- **Chat**: 30 requests/minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## Input Validation

All inputs are validated:
- **Ethereum addresses**: Checksum validation, format validation
- **Scores**: Range 0-1000
- **Risk bands**: Range 0-3
- **Messages**: Length limits, HTML sanitization

## Secrets Management

Private keys can be stored encrypted:

1. **Encrypt a secret:**
```python
from utils.secrets_manager import get_secrets_manager
manager = get_secrets_manager()
encrypted = manager.encrypt("your-private-key")
```

2. **Set in environment:**
```bash
BACKEND_PRIVATE_KEY_ENCRYPTED=<encrypted-value>
SECRETS_ENCRYPTION_KEY=<32-byte-key>
```

3. **Service automatically decrypts on startup**

## Security Headers

All responses include:
- `Content-Security-Policy`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (production only)

## Audit Logging

All sensitive operations are logged to `logs/audit.log`:
- Score generation
- On-chain updates
- Loan creation
- Admin actions

Log format (JSON):
```json
{
  "timestamp": "2025-01-01T00:00:00",
  "user_address": "0x...",
  "action": "generate_score",
  "endpoint": "POST /api/score",
  "ip_address": "1.2.3.4",
  "result": "success",
  "metadata": {...}
}
```

## Replay Attack Prevention

Nonces and timestamps prevent replay attacks:
- Each request includes a nonce
- Messages expire after 5 minutes
- Used nonces are tracked (Redis or in-memory)

## CORS Configuration

CORS is configured via `FRONTEND_URL` environment variable:
```bash
FRONTEND_URL=https://your-frontend.com
```

In production, never use `allow_origins=["*"]`.

## Best Practices

1. **Never commit secrets** - Use encrypted secrets or environment variables
2. **Rotate API keys regularly** - Update `API_KEYS` periodically
3. **Monitor audit logs** - Review `logs/audit.log` for suspicious activity
4. **Use HTTPS** - Always use HTTPS in production
5. **Set strong JWT secret** - Use a cryptographically random secret
6. **Enable Redis** - For distributed rate limiting in production

## Environment Variables

See `backend/.env.example` for all required environment variables.



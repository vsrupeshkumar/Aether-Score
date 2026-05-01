# Security Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate Security Keys

Run the setup script:

```bash
python3 scripts/setup_security.py
```

This will generate:
- `SECRETS_ENCRYPTION_KEY` - For encrypting private keys
- `JWT_SECRET_KEY` - For JWT token signing
- `API_KEYS` - Example API key

Copy these values to your `.env` file.

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

**Required variables:**
- `CREDIT_PASSPORT_NFT_ADDRESS` - Your deployed contract address
- `BACKEND_PRIVATE_KEY` - Backend wallet private key
- `QIE_RPC_URL` - QIE blockchain RPC URL

**Security variables (from setup script):**
- `SECRETS_ENCRYPTION_KEY` - Encryption key
- `JWT_SECRET_KEY` - JWT secret
- `API_KEYS` - Comma-separated API keys

**Optional:**
- `FRONTEND_URL` - Your frontend URL (defaults to localhost:3000)
- `REDIS_URL` - Redis URL for distributed rate limiting
- `RATE_LIMIT_ENABLED` - Enable/disable rate limiting (default: true)

### 4. Test Security Setup

```bash
python3 scripts/test_security.py
```

This will verify:
- All modules can be imported
- Validators work correctly
- Secrets manager encrypts/decrypts
- JWT tokens generate and verify
- API keys validate
- Environment variables are set

### 5. Start Backend

```bash
python3 -m uvicorn app:app --reload
```

## Authentication Methods

### Method 1: API Key

```bash
curl -H "Authorization: ApiKey your-api-key" \
  http://localhost:8000/api/score \
  -d '{"address": "0x..."}'
```

### Method 2: JWT Token

First, get a token:

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0x...",
    "signature": "0x...",
    "message": "AETHER-SCORE Authentication\n..."
  }'
```

Then use the token:

```bash
curl -H "Authorization: Bearer <jwt-token>" \
  http://localhost:8000/api/score \
  -d '{"address": "0x..."}'
```

### Method 3: Wallet Signature (in request body)

```bash
curl -X POST http://localhost:8000/api/score \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0x...",
    "signature": "0x...",
    "message": "...",
    "timestamp": 1234567890
  }'
```

## Rate Limits

- **Per IP**: 60 requests/minute, 1000 requests/hour
- **Score Generation**: 10 requests/minute
- **Chat**: 30 requests/minute
- **Other endpoints**: 60 requests/minute

Rate limit headers in response:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## Encrypting Private Keys

To encrypt your private keys:

```python
from utils.secrets_manager import get_secrets_manager

manager = get_secrets_manager()
encrypted = manager.encrypt("your-private-key-here")
print(f"BACKEND_PRIVATE_KEY_ENCRYPTED={encrypted}")
```

Add to `.env`:
```bash
BACKEND_PRIVATE_KEY_ENCRYPTED=<encrypted-value>
SECRETS_ENCRYPTION_KEY=<your-encryption-key>
```

## Audit Logs

Audit logs are written to `logs/audit.log` in JSON format.

View logs:
```bash
tail -f logs/audit.log | jq
```

## Troubleshooting

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (should be 3.10+)

### Authentication Fails
- Verify API key is in `API_KEYS` env var (comma-separated)
- Check JWT secret is set correctly
- Verify wallet signature format (must be 0x + 130 hex chars)

### Rate Limiting Issues
- Check `RATE_LIMIT_ENABLED=true` in `.env`
- If using Redis, verify `REDIS_URL` is correct
- Check rate limit headers in response

### Secrets Manager Errors
- Ensure `SECRETS_ENCRYPTION_KEY` is set
- If using encrypted secrets, verify encryption key matches
- Check that encrypted values are valid base64

## Production Checklist

- [ ] Generate strong encryption key (32 bytes)
- [ ] Generate strong JWT secret (32+ characters)
- [ ] Set unique API keys for each service
- [ ] Use encrypted private keys
- [ ] Set `FRONTEND_URL` to production domain
- [ ] Set `ENVIRONMENT=production`
- [ ] Enable Redis for distributed rate limiting
- [ ] Configure log rotation for audit logs
- [ ] Set up monitoring for security events
- [ ] Review and rotate keys periodically



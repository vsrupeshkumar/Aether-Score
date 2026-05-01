# AETHER-SCORE Public API Documentation

## Overview

The AETHER-SCORE Public API provides programmatic access to credit scores, loan data, and portfolio information. All endpoints require API key authentication.

**Base URL**: `https://AETHER-SCORE-backend.onrender.com`

**API Version**: `v1`

## Authentication

All API requests require an API key in the request header:

```
X-API-Key: your-api-key-here
```

Or via Authorization header:

```
Authorization: Bearer your-api-key-here
```

## Rate Limits

- **Free Tier**: 100 requests/day, 10 requests/minute
- **Paid Tier**: 10,000 requests/day, 100 requests/minute
- **Enterprise**: Custom limits

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per period
- `X-RateLimit-Remaining`: Remaining requests in current period
- `X-RateLimit-Reset`: Unix timestamp when rate limit resets

## Endpoints

### Get Credit Score

Get the current credit score for a wallet address.

**Endpoint**: `GET /api/v1/score/{address}`

**Parameters**:
- `address` (path, required): Wallet address (0x...)

**Response**:
```json
{
  "address": "0x...",
  "score": 750,
  "risk_band": 1,
  "last_updated": "2025-12-18T12:00:00Z"
}
```

### Get Score History

Get historical credit scores for a wallet address.

**Endpoint**: `GET /api/v1/score/{address}/history`

**Parameters**:
- `address` (path, required): Wallet address
- `limit` (query, optional): Maximum number of entries (default: 30, max: 100)

**Response**:
```json
{
  "address": "0x...",
  "history": [
    {
      "score": 750,
      "risk_band": 1,
      "computed_at": "2025-12-18T12:00:00Z"
    }
  ]
}
```

### Get Loans

Get loan information for a wallet address.

**Endpoint**: `GET /api/v1/loans/{address}`

**Parameters**:
- `address` (path, required): Wallet address

**Response**:
```json
{
  "address": "0x...",
  "loans": [
    {
      "id": 1,
      "amount": 1000,
      "interest_rate": 5.0,
      "status": "active",
      "created_at": "2025-12-18T12:00:00Z"
    }
  ]
}
```

### Get Portfolio

Get portfolio data for a wallet address.

**Endpoint**: `GET /api/v1/portfolio/{address}`

**Parameters**:
- `address` (path, required): Wallet address

**Response**:
```json
{
  "address": "0x...",
  "total_value": 5000.50,
  "holdings": [
    {
      "token": "QIE",
      "balance": 1000,
      "value_usd": 5000
    }
  ]
}
```

### Register Webhook

Register a webhook to receive event notifications.

**Endpoint**: `POST /api/v1/webhooks`

**Request Body**:
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["score.updated", "loan.created"]
}
```

**Response**:
```json
{
  "id": 1,
  "url": "https://your-app.com/webhook",
  "events": ["score.updated", "loan.created"],
  "secret": "webhook-secret-here",
  "created_at": "2025-12-18T12:00:00Z"
}
```

**Available Events**:
- `score.updated` - Credit score changed
- `loan.created` - New loan created
- `loan.repaid` - Loan repaid
- `loan.defaulted` - Loan defaulted
- `achievement.unlocked` - Achievement unlocked

### Delete Webhook

Delete a registered webhook.

**Endpoint**: `DELETE /api/v1/webhooks/{webhook_id}`

**Parameters**:
- `webhook_id` (path, required): Webhook ID

**Response**:
```json
{
  "success": true
}
```

## Webhook Verification

Webhooks include an HMAC-SHA256 signature in the `X-AETHER-SCORE-Signature` header. Verify signatures using your webhook secret:

**JavaScript**:
```javascript
const crypto = require('crypto');
const hmac = crypto.createHmac('sha256', secret);
const signature = `sha256=${hmac.update(JSON.stringify(payload)).digest('hex')}`;
```

**Python**:
```python
import hmac
import hashlib
import json

payload_str = json.dumps(payload, sort_keys=True)
signature = f"sha256={hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()}"
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**Status Codes**:
- `400` - Bad Request
- `401` - Unauthorized (invalid API key)
- `404` - Not Found
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

## SDKs

Official SDKs are available:

- **JavaScript/TypeScript**: `npm install @AETHER-SCORE/sdk`
- **Python**: `pip install AETHER-SCORE-sdk`

See SDK documentation for usage examples.

## Support

For API support, contact: api@AETHER-SCORE.io


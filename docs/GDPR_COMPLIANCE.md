# GDPR Compliance

This document outlines GDPR compliance features implemented in AETHER-SCORE.

## Overview

AETHER-SCORE implements GDPR (General Data Protection Regulation) compliance features to protect user privacy and data rights.

## GDPR Rights Implemented

### 1. Right to Access (Data Portability)

Users can request and receive a copy of all their personal data in a structured, machine-readable format (JSON).

**API Endpoint**: `POST /api/gdpr/export`

**Request**:
```json
{
  "address": "0x..."
}
```

**Response**:
```json
{
  "request_id": 123,
  "status": "completed",
  "export_file": "/tmp/gdpr_exports/export_0x..._20250101_120000.json",
  "data": {
    "wallet_address": "0x...",
    "exported_at": "2025-01-01T12:00:00",
    "user": {...},
    "scores": [...],
    "score_history": [...],
    "loans": [...],
    "transactions": [...]
  }
}
```

### 2. Right to Deletion (Right to be Forgotten)

Users can request deletion of their personal data. Deletion is processed after a 30-day grace period to allow for recovery if requested in error.

**API Endpoint**: `POST /api/gdpr/delete`

**Request**:
```json
{
  "address": "0x..."
}
```

**Response**:
```json
{
  "request_id": 124,
  "status": "pending",
  "grace_period_days": 30,
  "message": "Deletion will be processed after 30 day grace period"
}
```

### 3. Consent Management

Users can manage their GDPR consent preferences.

**Fields in User Model**:
- `gdpr_consent`: Boolean indicating consent
- `consent_date`: Timestamp of consent
- `data_deletion_requested`: Boolean indicating deletion request
- `deletion_requested_at`: Timestamp of deletion request

## Implementation Details

### Data Export

The export includes:
- User profile data
- Credit scores and history
- Loan records
- Transaction history
- All associated metadata

### Data Deletion

Deletion process:
1. User requests deletion
2. Request is logged in `gdpr_requests` table
3. User is marked for deletion (`data_deletion_requested = true`)
4. After 30-day grace period, data is soft-deleted
5. Soft delete maintains referential integrity while removing user data

### Grace Period

The 30-day grace period allows:
- Users to cancel deletion requests
- Recovery of accidentally deleted accounts
- Compliance with financial data retention requirements

## Automated Processing

GDPR deletion requests are processed automatically:
- **Schedule**: Daily at 2 AM UTC (via Kubernetes CronJob)
- **Service**: `GDPRService.process_deletion_requests()`
- **Grace Period**: 30 days (configurable via `GDPR_DELETION_GRACE_PERIOD_DAYS`)

## Configuration

Environment variables:
```bash
GDPR_DELETION_GRACE_PERIOD_DAYS=30
GDPR_EXPORT_DIR=/tmp/gdpr_exports
```

## Security

- All GDPR endpoints require authentication
- Rate limiting: 5 requests/minute for deletion/export
- Audit logging for all GDPR operations
- Export files are stored securely (in production, use S3 or similar)

## Compliance Checklist

- âœ… Right to access (data export)
- âœ… Right to deletion (with grace period)
- âœ… Consent management
- âœ… Data portability (JSON export)
- âœ… Audit logging
- âœ… Secure data handling

## Future Enhancements

- [ ] Consent withdrawal mechanism
- [ ] Data rectification endpoint
- [ ] Automated consent reminders
- [ ] Integration with privacy policy updates
- [ ] S3 export storage for large datasets

## References

- [GDPR Official Text](https://gdpr-info.eu/)
- [ICO GDPR Guide](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/)



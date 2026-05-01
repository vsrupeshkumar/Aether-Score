# Data Validation

This document outlines data validation and integrity checks in AETHER-SCORE.

## Overview

AETHER-SCORE implements comprehensive data validation at multiple levels:
- Database constraints
- Application-level validation
- Data integrity checks
- Constraint violation detection

## Database Constraints

### Check Constraints

- **Users**: Wallet address format validation
- **Loans**: Amount > 0, interest rate 0-100%, term days > 0, valid status
- **Loan Payments**: Amount > 0, valid payment type
- **Transactions**: Valid transaction status
- **GDPR Requests**: Valid request type and status

### Foreign Key Constraints

- `scores.wallet_address` â†’ `users.wallet_address`
- `score_history.wallet_address` â†’ `scores.wallet_address`
- `loans.wallet_address` â†’ `users.wallet_address`
- `loan_payments.loan_id` â†’ `loans.id`
- `transactions.wallet_address` â†’ `users.wallet_address`
- `gdpr_requests.wallet_address` â†’ `users.wallet_address`

### Unique Constraints

- `transactions.tx_hash` (unique)
- `users.wallet_address` (primary key)
- `scores.wallet_address` (primary key)

## Application-Level Validation

### Validation Service

The `DataValidationService` provides:
- User data validation
- Loan data validation
- Transaction data validation
- Foreign key integrity checks
- Constraint violation detection

### Usage

```python
from services.validation import DataValidationService

service = DataValidationService()

# Validate user data
errors = await service.validate_user_data({
    "wallet_address": "0x...",
    "email": "user@example.com"
})

# Check data integrity
results = await service.validate_all_data()
```

## Integrity Checks

### Foreign Key Integrity

Checks for orphaned records:
- Scores without users
- Loans without users
- Transactions without users
- Loan payments without loans

### Constraint Violations

Detects:
- Invalid loan amounts
- Invalid interest rates
- Invalid loan statuses
- Invalid payment types

## Running Integrity Checks

### Manual Check

```bash
./scripts/check-data-integrity.sh [environment]
```

### Automated Checks

Integrity checks can be scheduled via:
- Kubernetes CronJob
- CI/CD pipeline
- Monitoring alerts

## Validation Rules

### Wallet Address

- Format: `0x` followed by 40 hex characters
- Regex: `^0x[a-fA-F0-9]{40}$`

### Loan Amount

- Must be > 0
- Decimal precision: 20, 8

### Interest Rate

- Range: 0-100%
- Decimal precision: 5, 2

### Term Days

- Must be > 0
- Integer type

### Loan Status

Valid values:
- `pending`
- `active`
- `repaid`
- `defaulted`
- `liquidated`

### Payment Type

Valid values:
- `principal`
- `interest`
- `both`

## Error Handling

Validation errors are:
- Logged with context
- Returned to API clients
- Tracked in audit logs

## Best Practices

1. **Validate Early**: Validate at API entry point
2. **Database Constraints**: Use database constraints as final check
3. **Regular Checks**: Run integrity checks regularly
4. **Monitor Violations**: Alert on constraint violations
5. **Document Rules**: Keep validation rules documented

## Troubleshooting

### Constraint Violations

1. Check validation service logs
2. Review constraint definitions
3. Verify data before insertion
4. Check foreign key relationships

### Integrity Issues

1. Run integrity check script
2. Review orphaned records
3. Fix data inconsistencies
4. Update validation rules if needed



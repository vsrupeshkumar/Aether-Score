# Data Archival

This document outlines the data archival strategy for AETHER-SCORE.

## Overview

Data archival moves old data from the active database to cold storage (S3 Glacier) to:
- Reduce database size
- Lower storage costs
- Maintain data for compliance
- Enable data recovery if needed

## Archival Strategy

### What Gets Archived

- **Score History**: Records older than 1 year
- **Transactions**: Records older than 1 year
- **Audit Logs**: Records older than 2 years (future)

### Archival Process

1. **Identify Old Data**: Records older than retention period
2. **Export to JSON**: Convert database records to JSON format
3. **Upload to S3**: Store in S3 Glacier for cost efficiency
4. **Delete from Database**: Remove archived records
5. **Log Action**: Record archival in `data_retention_log`

## Storage

### S3 Configuration

- **Bucket**: Configured via `ARCHIVE_S3_BUCKET`
- **Storage Class**: Glacier (for cost savings)
- **Path Structure**: `{table_name}/{year}/{month}/batch_{offset}.json`

### Archive Format

```json
[
  {
    "id": 1,
    "wallet_address": "0x...",
    "score": 750,
    "risk_band": 2,
    "timestamp": "2024-01-01T00:00:00"
  },
  ...
]
```

## Archival Service

### Usage

```python
from services.archival import ArchivalService

service = ArchivalService()

# Archive score history
result = await service.archive_score_history(
    cutoff_date=datetime.utcnow() - timedelta(days=365)
)

# Archive transactions
result = await service.archive_transactions(
    cutoff_date=datetime.utcnow() - timedelta(days=365)
)
```

### Integration with Retention Service

The retention service automatically archives data before deletion:

```python
from services.retention import DataRetentionService

service = DataRetentionService()
results = await service.cleanup_all(archive=True)
```

## Restore Procedures

### Restore from Archive

1. **Identify Archive File**
   ```bash
   aws s3 ls s3://{bucket}/score_history/2024/01/
   ```

2. **Download Archive**
   ```bash
   aws s3 cp s3://{bucket}/score_history/2024/01/batch_0.json ./restore.json
   ```

3. **Restore to Database**
   ```python
   from services.archival import ArchivalService
   
   service = ArchivalService()
   result = await service.restore_from_archive(
       archive_key="score_history/2024/01/batch_0.json",
       table_name="score_history"
   )
   ```

## Configuration

### Environment Variables

```bash
ARCHIVE_S3_BUCKET=AETHER-SCORE-archives
AWS_REGION=us-east-1
ARCHIVE_RETENTION_DAYS=365
```

### AWS Permissions

Required IAM permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::AETHER-SCORE-archives/*",
        "arn:aws:s3:::AETHER-SCORE-archives"
      ]
    }
  ]
}
```

## Cost Optimization

### S3 Storage Classes

- **Standard**: Active data (not used for archives)
- **Glacier**: Archived data (used by default)
- **Deep Archive**: Long-term archives (optional)

### Lifecycle Policies

Configure S3 lifecycle policies to:
- Move to Glacier after 30 days
- Move to Deep Archive after 90 days
- Delete after retention period

Example lifecycle policy:
```json
{
  "Rules": [
    {
      "Id": "ArchiveToGlacier",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

## Monitoring

### Archival Metrics

Track:
- Records archived per day
- Archive size
- S3 upload success rate
- Archive restore requests

### Alerts

Set up alerts for:
- Archival failures
- S3 upload failures
- Archive size anomalies

## Best Practices

1. **Test Archival**: Regularly test archival process
2. **Verify Archives**: Verify archived data integrity
3. **Document Restores**: Keep restore procedures updated
4. **Monitor Costs**: Track S3 storage costs
5. **Retention Policy**: Enforce retention periods consistently

## Troubleshooting

### Archival Fails

1. Check S3 connectivity
2. Verify AWS credentials
3. Check S3 bucket permissions
4. Review service logs

### Restore Fails

1. Verify archive file exists
2. Check S3 permissions
3. Verify JSON format
4. Check database connectivity

## References

- [AWS S3 Glacier](https://aws.amazon.com/s3/glacier/)
- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [S3 Storage Classes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html)



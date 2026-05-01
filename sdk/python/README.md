# AETHER-SCORE Python SDK

Official Python SDK for integrating AETHER-SCORE credit scores into your application.

## Installation

```bash
pip install AETHER-SCORE-sdk
```

## Usage

```python
from aether_score import AetherScoreClient

client = AetherScoreClient(
    api_key='your-api-key',
    base_url='https://aether-score-backend.onrender.com'  # Optional
)

# Get credit score
score = client.get_score('0x...')

# Get score history
history = client.get_score_history('0x...', limit=30)

# Get loans
loans = client.get_loans('0x...')

# Register webhook
webhook = client.register_webhook(
    url='https://your-app.com/webhook',
    events=['score.updated', 'loan.created']
)

# Verify webhook signature
is_valid = client.verify_webhook_signature(
    payload,
    signature,
    secret
)
```

## API Reference

See [AETHER-SCORE API Documentation](https://AETHER-SCORE-backend.onrender.com/docs) for full API reference.



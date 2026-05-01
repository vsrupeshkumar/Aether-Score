# AETHER-SCORE JavaScript/TypeScript SDK

Official SDK for integrating AETHER-SCORE credit scores into your application.

## Installation

```bash
npm install @AETHER-SCORE/sdk
```

## Usage

```typescript
import AETHER-SCORESDK from '@AETHER-SCORE/sdk';

const sdk = new AETHER-SCORESDK({
  apiKey: 'your-api-key',
  baseURL: 'https://AETHER-SCORE-backend.onrender.com', // Optional
});

// Get credit score
const score = await sdk.getScore('0x...');

// Get score history
const history = await sdk.getScoreHistory('0x...', 30);

// Get loans
const loans = await sdk.getLoans('0x...');

// Register webhook
const webhook = await sdk.registerWebhook({
  url: 'https://your-app.com/webhook',
  events: ['score.updated', 'loan.created'],
});

// Verify webhook signature
const isValid = sdk.verifyWebhookSignature(
  payload,
  signature,
  secret
);
```

## API Reference

See [AETHER-SCORE API Documentation](https://AETHER-SCORE-backend.onrender.com/docs) for full API reference.



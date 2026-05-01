# AETHER-SCORE Integration Guide

This guide provides step-by-step instructions for integrating AETHER-SCORE into your application, including API integration, smart contract integration, and SDK usage.

## Table of Contents

- [Quick Start](#quick-start)
- [API Integration](#api-integration)
- [Smart Contract Integration](#smart-contract-integration)
- [SDK Usage](#sdk-usage)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Quick Start

### 1. Get API Credentials

1. Sign up at [https://app.AETHER-SCORE.io](https://app.AETHER-SCORE.io)
2. Navigate to Settings â†’ API Keys
3. Generate a new API key
4. Store it securely (never commit to version control)

### 2. Install SDK (Optional)

```bash
# Python
pip install AETHER-SCORE-sdk

# JavaScript/TypeScript
npm install @AETHER-SCORE/sdk

# Or use direct API calls
```

### 3. Make Your First Request

```python
# Python
from AETHER-SCORE import AETHER-SCOREClient

client = AETHER-SCOREClient(api_key="your-api-key")
score = client.get_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"Credit Score: {score['score']}")
```

```javascript
// JavaScript
import { AETHER-SCOREClient } from '@AETHER-SCORE/sdk';

const client = new AETHER-SCOREClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.AETHER-SCORE.io'
});

const score = await client.getScore('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
console.log(`Credit Score: ${score.score}`);
```

## API Integration

### Authentication

Choose one of three authentication methods:

#### Method 1: API Key (Recommended for Server-Side)

```python
import requests

headers = {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}

response = requests.get(
    "https://api.AETHER-SCORE.io/api/score/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    headers=headers
)
```

#### Method 2: JWT Token (Recommended for User-Facing Apps)

```python
# Step 1: Get JWT token
auth_response = requests.post(
    "https://api.AETHER-SCORE.io/api/auth/token",
    json={
        "address": user_wallet_address,
        "message": signed_message,
        "signature": signature
    }
)
token = auth_response.json()["access_token"]

# Step 2: Use token
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

#### Method 3: Wallet Signature (For Blockchain Operations)

```python
response = requests.post(
    "https://api.AETHER-SCORE.io/api/score",
    json={
        "address": wallet_address,
        "signature": signature,
        "message": message,
        "timestamp": timestamp
    }
)
```

### Core Endpoints

#### Get Credit Score

```python
# GET /api/score/{address}
response = requests.get(
    f"https://api.AETHER-SCORE.io/api/score/{wallet_address}",
    headers=headers
)
score_data = response.json()
```

#### Generate New Score

```python
# POST /api/score
response = requests.post(
    "https://api.AETHER-SCORE.io/api/score",
    headers=headers,
    json={"address": wallet_address}
)
score_data = response.json()
```

#### Get Staking Information

```python
# GET /api/staking/{address}
response = requests.get(
    f"https://api.AETHER-SCORE.io/api/staking/{wallet_address}",
    headers=headers
)
staking_data = response.json()
```

#### Get Loan-to-Value (LTV)

```python
# GET /api/lending/ltv/{address}
response = requests.get(
    f"https://api.AETHER-SCORE.io/api/lending/ltv/{wallet_address}",
    headers=headers
)
ltv_data = response.json()
```

### Rate Limiting

Handle rate limits gracefully:

```python
import time

def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:
            # Rate limited
            retry_after = int(response.headers.get("Retry-After", 60))
            if attempt < max_retries - 1:
                time.sleep(retry_after)
                continue
            else:
                raise Exception("Rate limit exceeded")
        
        return response.json()
    
    raise Exception("Max retries exceeded")
```

## Smart Contract Integration

### Deployed Contracts

**QIE Testnet**:
- CreditPassportNFT: `0x...`
- AETHER-SCOREStaking: `0x...`
- LendingVault: `0x...`

**QIE Mainnet**:
- CreditPassportNFT: `0x...`
- AETHER-SCOREStaking: `0x...`
- LendingVault: `0x...`

### Reading Credit Scores On-Chain

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/interfaces/IERC721.sol";
import "./IAETHER-SCOREScore.sol";

contract MyContract {
    IAETHER-SCOREScore public creditPassport;
    
    constructor(address _creditPassport) {
        creditPassport = IAETHER-SCOREScore(_creditPassport);
    }
    
    function checkCreditScore(address user) external view returns (uint256 score, uint8 riskBand) {
        // Check if user has a credit passport NFT
        require(IERC721(address(creditPassport)).balanceOf(user) > 0, "No credit passport");
        
        // Get token ID (assuming one NFT per user)
        uint256 tokenId = creditPassport.tokenOfOwnerByIndex(user, 0);
        
        // Get score and risk band
        score = creditPassport.getScore(tokenId);
        riskBand = creditPassport.getRiskBand(tokenId);
    }
}
```

### Using Credit Scores in Your Contract

```solidity
contract LendingContract {
    IAETHER-SCOREScore public creditPassport;
    
    mapping(uint8 => uint256) public ltvByRiskBand;
    
    constructor(address _creditPassport) {
        creditPassport = IAETHER-SCOREScore(_creditPassport);
        ltvByRiskBand[0] = 8000; // 80% for very low risk
        ltvByRiskBand[1] = 7000; // 70% for low risk
        ltvByRiskBand[2] = 5000; // 50% for moderate risk
        ltvByRiskBand[3] = 3000; // 30% for high risk
    }
    
    function calculateMaxLoan(address borrower, uint256 collateralValue) 
        external 
        view 
        returns (uint256) 
    {
        // Get risk band
        uint256 tokenId = creditPassport.tokenOfOwnerByIndex(borrower, 0);
        uint8 riskBand = creditPassport.getRiskBand(tokenId);
        
        // Calculate max loan based on LTV
        uint256 ltv = ltvByRiskBand[riskBand];
        return (collateralValue * ltv) / 10000;
    }
}
```

### JavaScript/TypeScript Integration

```typescript
import { ethers } from "ethers";
import CreditPassportNFT from "./abis/CreditPassportNFT.json";

const provider = new ethers.JsonRpcProvider("https://rpc1testnet.qie.digital/");
const contract = new ethers.Contract(
  "0x...", // CreditPassportNFT address
  CreditPassportNFT.abi,
  provider
);

// Get score for a wallet
async function getScore(walletAddress: string) {
  // Check if user has NFT
  const balance = await contract.balanceOf(walletAddress);
  if (balance === 0n) {
    throw new Error("No credit passport found");
  }

  // Get token ID
  const tokenId = await contract.tokenOfOwnerByIndex(walletAddress, 0);

  // Get score and risk band
  const score = await contract.getScore(tokenId);
  const riskBand = await contract.getRiskBand(tokenId);

  return { score: Number(score), riskBand: Number(riskBand) };
}
```

### Staking Integration

```typescript
import AETHER-SCOREStaking from "./abis/AETHER-SCOREStaking.json";

const stakingContract = new ethers.Contract(
  "0x...", // Staking contract address
  AETHER-SCOREStaking.abi,
  signer // Wallet with private key
);

// Stake tokens
async function stake(amount: bigint) {
  const tx = await stakingContract.stake(amount);
  await tx.wait();
  console.log("Staked successfully");
}

// Get staking info
async function getStakingInfo(walletAddress: string) {
  const stakedAmount = await stakingContract.getStakedAmount(walletAddress);
  const tier = await stakingContract.getTier(walletAddress);
  return { stakedAmount, tier };
}
```

## SDK Usage

### Python SDK

```python
from AETHER-SCORE import AETHER-SCOREClient
from web3 import Web3

# Initialize client
client = AETHER-SCOREClient(
    api_key="your-api-key",
    base_url="https://api.AETHER-SCORE.io"
)

# Get score
score = client.get_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"Score: {score['score']}, Risk Band: {score['riskBand']}")

# Generate new score
result = client.generate_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"New Score: {result['score']}")

# Get staking info
staking = client.get_staking_info("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"Tier: {staking['tierName']}, Boost: {staking['scoreBoost']}")

# Get LTV
ltv = client.get_ltv("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"LTV: {ltv['ltvPercent']}%")
```

### JavaScript SDK

```typescript
import { AETHER-SCOREClient } from '@AETHER-SCORE/sdk';

const client = new AETHER-SCOREClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.AETHER-SCORE.io'
});

// Get score
const score = await client.getScore('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
console.log(`Score: ${score.score}, Risk Band: ${score.riskBand}`);

// Generate new score
const result = await client.generateScore('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
console.log(`New Score: ${result.score}`);

// Get staking info
const staking = await client.getStakingInfo('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
console.log(`Tier: ${staking.tierName}, Boost: ${staking.scoreBoost}`);

// Get LTV
const ltv = await client.getLTV('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb');
console.log(`LTV: ${ltv.ltvPercent}%`);
```

## Best Practices

### 1. Caching

Cache credit scores to reduce API calls:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedAETHER-SCOREClient:
    def __init__(self, api_key):
        self.client = AETHER-SCOREClient(api_key=api_key)
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
    
    def get_score(self, address):
        now = datetime.now()
        
        if address in self.cache:
            cached_data, cached_time = self.cache[address]
            if now - cached_time < self.cache_ttl:
                return cached_data
        
        # Fetch fresh data
        score_data = self.client.get_score(address)
        self.cache[address] = (score_data, now)
        return score_data
```

### 2. Error Handling

Always handle errors gracefully:

```python
try:
    score = client.get_score(wallet_address)
except AETHER-SCOREAPIError as e:
    if e.status_code == 404:
        # No score found, generate new one
        score = client.generate_score(wallet_address)
    elif e.status_code == 429:
        # Rate limited, retry later
        time.sleep(60)
        score = client.get_score(wallet_address)
    else:
        # Log and handle other errors
        logger.error(f"API error: {e}")
        raise
```

### 3. Batch Operations

For multiple addresses, use batch endpoints when available:

```python
# Instead of:
scores = []
for address in addresses:
    scores.append(client.get_score(address))

# Use batch endpoint:
scores = client.get_scores_batch(addresses)
```

### 4. Webhook Integration

Set up webhooks for real-time updates:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhooks/AETHER-SCORE', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-AETHER-SCORE-Signature')
    payload = request.json
    
    # Verify signature
    if not verify_webhook_signature(payload, signature):
        return "Invalid signature", 401
    
    event_type = payload['event']
    
    if event_type == 'score.updated':
        handle_score_update(payload['data'])
    elif event_type == 'loan.created':
        handle_loan_created(payload['data'])
    
    return "OK", 200
```

## Error Handling

### Common Errors

| Error Code | Description | Solution |
|-----------|-------------|----------|
| `INVALID_ADDRESS` | Invalid Ethereum address | Validate address format |
| `AUTH_REQUIRED` | Missing authentication | Add API key or JWT token |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement retry with backoff |
| `SCORE_NOT_FOUND` | No score for address | Generate new score |
| `BLOCKCHAIN_ERROR` | Blockchain transaction failed | Check network status |

### Retry Logic

```python
import time
from functools import wraps

def retry_on_rate_limit(max_retries=3, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except AETHER-SCOREAPIError as e:
                    if e.status_code == 429 and attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        time.sleep(wait_time)
                        continue
                    raise
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

@retry_on_rate_limit()
def get_score_with_retry(address):
    return client.get_score(address)
```

## Examples

### Example 1: Lending Platform Integration

```python
from AETHER-SCORE import AETHER-SCOREClient
from web3 import Web3

class LendingPlatform:
    def __init__(self, api_key, rpc_url):
        self.cred_client = AETHER-SCOREClient(api_key=api_key)
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
    
    def calculate_loan_terms(self, borrower_address, collateral_value):
        # Get credit score
        score_data = self.cred_client.get_score(borrower_address)
        risk_band = score_data['riskBand']
        
        # Get LTV based on risk band
        ltv_data = self.cred_client.get_ltv(borrower_address)
        max_loan = (collateral_value * ltv_data['ltvPercent']) / 100
        
        # Calculate interest rate based on risk
        interest_rates = {0: 0.03, 1: 0.05, 2: 0.08, 3: 0.12}
        interest_rate = interest_rates.get(risk_band, 0.12)
        
        return {
            "max_loan": max_loan,
            "interest_rate": interest_rate,
            "risk_band": risk_band,
            "score": score_data['score']
        }
```

### Example 2: DeFi Protocol Integration

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IAETHER-SCOREScore.sol";

contract DeFiProtocol {
    IAETHER-SCOREScore public creditPassport;
    
    mapping(uint8 => uint256) public collateralRatios;
    
    constructor(address _creditPassport) {
        creditPassport = IAETHER-SCOREScore(_creditPassport);
        collateralRatios[0] = 120; // 120% for very low risk
        collateralRatios[1] = 150; // 150% for low risk
        collateralRatios[2] = 200; // 200% for moderate risk
        collateralRatios[3] = 300; // 300% for high risk
    }
    
    function borrow(address borrower, uint256 amount) external {
        // Get risk band
        uint256 tokenId = creditPassport.tokenOfOwnerByIndex(borrower, 0);
        uint8 riskBand = creditPassport.getRiskBand(tokenId);
        
        // Calculate required collateral
        uint256 requiredCollateral = (amount * collateralRatios[riskBand]) / 100;
        
        // Check collateral
        require(
            getCollateralBalance(borrower) >= requiredCollateral,
            "Insufficient collateral"
        );
        
        // Execute borrow
        // ...
    }
}
```

### Example 3: Frontend Integration

```typescript
import { AETHER-SCOREClient } from '@AETHER-SCORE/sdk';
import { ethers } from 'ethers';

export class CreditScoreWidget {
  private client: AETHER-SCOREClient;
  private provider: ethers.Provider;

  constructor(apiKey: string, rpcUrl: string) {
    this.client = new AETHER-SCOREClient({ apiKey, baseURL: 'https://api.AETHER-SCORE.io' });
    this.provider = new ethers.JsonRpcProvider(rpcUrl);
  }

  async displayScore(walletAddress: string): Promise<void> {
    try {
      // Get score from API
      const scoreData = await this.client.getScore(walletAddress);
      
      // Display score
      this.updateUI({
        score: scoreData.score,
        riskBand: this.getRiskBandName(scoreData.riskBand),
        stakingBoost: scoreData.stakingBoost
      });
    } catch (error) {
      if (error.statusCode === 404) {
        // No score found, generate new one
        const newScore = await this.client.generateScore(walletAddress);
        this.displayScore(walletAddress);
      } else {
        this.showError(error.message);
      }
    }
  }

  private getRiskBandName(riskBand: number): string {
    const names = ['Very Low', 'Low', 'Moderate', 'High'];
    return names[riskBand] || 'Unknown';
  }
}
```

## Support

- **Documentation**: https://docs.AETHER-SCORE.io
- **API Reference**: https://docs.AETHER-SCORE.io/api
- **GitHub**: https://github.com/AETHER-SCORE/AETHER-SCORE
- **Discord**: https://discord.gg/AETHER-SCORE
- **Email**: support@AETHER-SCORE.io



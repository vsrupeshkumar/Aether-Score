# Data Flow Documentation

## Overview

This document describes how data flows through the AETHER-SCORE system, from user interactions to blockchain transactions and back.

## Credit Score Data Flow

### 1. Score Generation Request

```
User â†’ Frontend â†’ API â†’ Feature Engineering â†’ ML Model â†’ Database â†’ Blockchain â†’ Response
```

**Detailed Steps:**

1. **User Action**: User connects wallet and requests score generation
2. **Frontend**: Sends POST request to `/api/score` with wallet address
3. **API Layer**: 
   - Validates wallet address
   - Checks rate limits
   - Authenticates request
4. **Feature Engineering**:
   - Queries transaction history from database
   - Fetches on-chain data (balance, token holdings)
   - Calculates features (transaction patterns, DeFi interactions, etc.)
5. **ML Model**:
   - Receives feature vector
   - Generates credit score prediction
   - Determines risk band
6. **Database**:
   - Stores score and feature vector
   - Creates score history entry
7. **Blockchain** (if new user):
   - Mints Credit Passport NFT
   - Updates on-chain score registry
8. **Response**: Returns score, risk band, and explanation to frontend

### 2. Score Recalculation Flow

```
Scheduler â†’ RQ Worker â†’ Transaction Indexer â†’ Feature Engineering â†’ ML Model â†’ Database
```

**Steps:**

1. **Scheduler**: Triggers daily batch recalculation
2. **RQ Worker**: Processes queue of users needing recalculation
3. **Transaction Indexer**: 
   - Fetches new transactions from blockchain
   - Parses and stores transaction data
   - Extracts token transfers
4. **Feature Engineering**: Recalculates features with new data
5. **ML Model**: Generates updated score
6. **Database**: Updates score and history

## Loan Creation Data Flow

### 1. AI Negotiation Flow

```
User â†’ Frontend â†’ AI Agent â†’ API â†’ Blockchain â†’ Response
```

**Steps:**

1. **User**: Initiates loan request via chat interface
2. **AI Agent**: 
   - Analyzes user's credit score
   - Generates loan offer (amount, interest, terms)
   - Presents offer to user
3. **User**: Accepts or negotiates terms
4. **API**: 
   - Validates loan parameters
   - Creates EIP-712 signature for AI agent
5. **Blockchain**:
   - Deploys loan contract
   - Transfers collateral
   - Emits LoanCreated event
6. **Database**: Stores loan record
7. **Response**: Returns loan confirmation

### 2. Loan Repayment Flow

```
User â†’ Frontend â†’ API â†’ Blockchain â†’ Database â†’ Response
```

**Steps:**

1. **User**: Initiates repayment
2. **API**: Validates repayment amount
3. **Blockchain**:
   - Executes repayment transaction
   - Updates loan status
   - Emits LoanRepaid event
4. **Database**: Updates loan record
5. **Response**: Confirms repayment

## Staking Data Flow

```
User â†’ Frontend â†’ Blockchain â†’ API â†’ Database â†’ Response
```

**Steps:**

1. **User**: Approves and stakes NCRD tokens
2. **Blockchain**:
   - Transfers tokens to staking contract
   - Updates staking tier
   - Emits Staked event
3. **API**: 
   - Monitors blockchain events
   - Calculates score boost
4. **Database**: Updates user staking record
5. **Response**: Returns updated score with boost

## Oracle Data Flow

```
Oracle Contract â†’ API â†’ Database â†’ Scoring Service
```

**Steps:**

1. **Oracle Contract**: Provides latest price data
2. **API**: 
   - Fetches price from oracle
   - Calculates volatility from price history
3. **Database**: Stores price history
4. **Scoring Service**: Uses oracle data in score calculation

## Fraud Detection Data Flow

```
Transaction Data â†’ Feature Engineering â†’ Fraud Detection â†’ Database
```

**Steps:**

1. **Transaction Data**: Collected from blockchain and database
2. **Feature Engineering**: Extracts behavioral patterns
3. **Fraud Detection**:
   - Analyzes for Sybil attacks
   - Detects suspicious patterns
   - Calculates fraud score
4. **Database**: Updates fraud score
5. **Scoring Service**: Adjusts credit score based on fraud risk

## Data Synchronization

### Real-time Updates

- **WebSocket**: For live score updates (future)
- **Event Listeners**: Monitor blockchain events
- **Polling**: Periodic checks for new transactions

### Batch Processing

- **Scheduled Jobs**: Daily score recalculations
- **Queue Workers**: Process background tasks
- **Data Archival**: Move old data to cold storage

## Error Handling Flow

```
Error â†’ Logging â†’ Monitoring â†’ Alerting â†’ Recovery
```

**Steps:**

1. **Error Occurs**: In any service layer
2. **Logging**: Structured JSON logs with context
3. **Monitoring**: Sentry captures error details
4. **Alerting**: Notifies team if critical
5. **Recovery**: Retry logic or fallback mechanisms



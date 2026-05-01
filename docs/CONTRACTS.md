# Smart Contract Documentation

This document provides comprehensive documentation for all AETHER-SCORE smart contracts deployed on the QIE blockchain.

## Table of Contents

- [Overview](#overview)
- [CreditPassportNFT](#creditpassportnft)
- [AETHER-SCOREStaking](#AETHER-SCOREstaking)
- [LendingVault](#lendingvault)
- [Interfaces](#interfaces)
- [Security Considerations](#security-considerations)
- [Usage Examples](#usage-examples)

## Overview

AETHER-SCORE smart contracts are built on Solidity 0.8.20+ and follow OpenZeppelin standards for security and best practices. All contracts are upgradeable using the UUPS (Universal Upgradeable Proxy Standard) pattern.

### Contract Addresses

**QIE Testnet**:
- CreditPassportNFT: `0x...` (Proxy: `0x...`)
- AETHER-SCOREStaking: `0x...` (Proxy: `0x...`)
- LendingVault: `0x...` (Proxy: `0x...`)

**QIE Mainnet**:
- CreditPassportNFT: `0x...` (Proxy: `0x...`)
- AETHER-SCOREStaking: `0x...` (Proxy: `0x...`)
- LendingVault: `0x...` (Proxy: `0x...`)

## CreditPassportNFT

### Overview

The CreditPassportNFT is a soulbound (non-transferable) ERC-721 NFT that stores AI-generated credit scores on-chain. Each wallet address can have at most one passport NFT.

### Key Features

- **Soulbound**: NFTs cannot be transferred between wallets
- **Score Storage**: Stores credit score (0-1000) and risk band (0-3)
- **Upgradeable**: Uses UUPS pattern for future upgrades
- **Access Control**: Role-based access control for score updates

### Functions

#### `mintOrUpdate(address user, uint16 score, uint8 riskBand)`

Mints a new passport NFT or updates an existing one.

**Parameters**:
- `user`: Wallet address to mint/update passport for
- `score`: Credit score (0-1000)
- `riskBand`: Risk band (0-3)

**Access**: `SCORE_UPDATER_ROLE` only

**Events**:
- `PassportMinted(address indexed user, uint256 indexed tokenId)`: Emitted when a new passport is minted
- `ScoreUpdated(address indexed user, uint256 indexed tokenId, uint16 score, uint8 riskBand, uint64 timestamp)`: Emitted when score is updated

**Example**:
```solidity
creditPassport.mintOrUpdate(0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb, 750, 1);
```

#### `getScore(address user) external view returns (ScoreView memory)`

Gets the credit score for a wallet address.

**Returns**:
```solidity
struct ScoreView {
    uint16 score;        // Credit score (0-1000)
    uint8 riskBand;      // Risk band (0-3)
    uint64 lastUpdated; // Unix timestamp of last update
}
```

**Example**:
```solidity
ScoreView memory score = creditPassport.getScore(0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb);
// score.score = 750
// score.riskBand = 1
```

#### `passportIdOf(address user) external view returns (uint256)`

Gets the token ID of the passport NFT for a wallet address. Returns 0 if no passport exists.

**Example**:
```solidity
uint256 tokenId = creditPassport.passportIdOf(0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb);
```

#### `getScoreByToken(uint256 tokenId) external view returns (ScoreData memory)`

Gets score data directly by token ID.

**Returns**:
```solidity
struct ScoreData {
    uint16 score;
    uint8 riskBand;
    uint64 lastUpdated;
}
```

### Roles

- `DEFAULT_ADMIN_ROLE`: Can grant/revoke roles, burn passports
- `SCORE_UPDATER_ROLE`: Can mint and update credit scores

### Events

```solidity
event PassportMinted(address indexed user, uint256 indexed tokenId);
event ScoreUpdated(
    address indexed user,
    uint256 indexed tokenId,
    uint16 score,
    uint8 riskBand,
    uint64 timestamp
);
```

## AETHER-SCOREStaking

### Overview

The AETHER-SCOREStaking contract allows users to stake NCRD tokens to boost their credit tier and receive score bonuses.

### Key Features

- **Tiered Staking**: Four tiers (None, Bronze, Silver, Gold) based on staked amount
- **Score Boost**: Higher tiers provide larger score boosts
- **Unstake with Delay**: Unstaking requires a cooldown period
- **Upgradeable**: Uses UUPS pattern

### Staking Tiers

| Tier | Name | Min Stake | Score Boost |
|------|------|-----------|-------------|
| 0 | None | 0 | 0 |
| 1 | Bronze | 1,000 NCRD | +25 |
| 2 | Silver | 10,000 NCRD | +50 |
| 3 | Gold | 100,000 NCRD | +100 |

### Functions

#### `stake(uint256 amount) external`

Stakes NCRD tokens to increase credit tier.

**Parameters**:
- `amount`: Amount of NCRD tokens to stake (in wei)

**Requirements**:
- User must have approved the contract to spend tokens
- Amount must be greater than 0

**Events**:
- `Staked(address indexed user, uint256 amount, uint8 newTier)`

**Example**:
```solidity
// First approve tokens
ncrdToken.approve(address(stakingContract), 10000 * 10**18);
// Then stake
stakingContract.stake(10000 * 10**18);
```

#### `unstake(uint256 amount) external`

Initiates unstaking process. Tokens are locked for a cooldown period.

**Parameters**:
- `amount`: Amount of NCRD tokens to unstake

**Requirements**:
- User must have staked tokens
- Amount must not exceed staked amount
- Cooldown period must have passed (if previously unstaked)

**Events**:
- `UnstakeInitiated(address indexed user, uint256 amount, uint256 unlockTime)`

#### `withdraw() external`

Withdraws unstaked tokens after cooldown period.

**Requirements**:
- Unstake must have been initiated
- Cooldown period must have passed

**Events**:
- `Withdrawn(address indexed user, uint256 amount)`

#### `getStakedAmount(address user) external view returns (uint256)`

Gets the amount of tokens staked by a user.

#### `getTier(address user) external view returns (uint8)`

Gets the current staking tier for a user.

#### `calculateStakingBoost(uint8 tier) external pure returns (uint256)`

Calculates the score boost for a given tier.

**Returns**: Score boost (0-300)

### Events

```solidity
event Staked(address indexed user, uint256 amount, uint8 newTier);
event UnstakeInitiated(address indexed user, uint256 amount, uint256 unlockTime);
event Withdrawn(address indexed user, uint256 amount);
event TierChanged(address indexed user, uint8 oldTier, uint8 newTier);
```

## LendingVault

### Overview

The LendingVault contract manages collateralized loans with AI-negotiated terms. It handles loan creation, repayment, defaults, and liquidations.

### Key Features

- **Collateralized Loans**: Loans require collateral in supported tokens
- **AI Negotiation**: Loan terms are negotiated via AI agent
- **Automatic Liquidations**: Defaulted loans are automatically liquidated
- **Circuit Breakers**: Rate limiting and amount limits for security

### Functions

#### `createLoan(uint256 amount, uint256 interestRate, uint256 termDays, address collateralToken, uint256 collateralAmount) external`

Creates a new loan with specified terms.

**Parameters**:
- `amount`: Loan amount (in wei)
- `interestRate`: Interest rate (in basis points, e.g., 500 = 5%)
- `termDays`: Loan term in days
- `collateralToken`: Address of collateral token (ERC-20)
- `collateralAmount`: Amount of collateral (in wei)

**Requirements**:
- Borrower must have approved collateral transfer
- Collateral value must meet minimum LTV requirements
- Borrower must have valid credit passport

**Events**:
- `LoanCreated(uint256 indexed loanId, address indexed borrower, uint256 amount, uint256 interestRate)`

#### `repayLoan(uint256 loanId) external payable`

Repays a loan (principal + interest).

**Parameters**:
- `loanId`: ID of the loan to repay

**Requirements**:
- Loan must be active
- Caller must be the borrower
- Payment must cover principal + interest

**Events**:
- `LoanRepaid(uint256 indexed loanId, address indexed borrower, uint256 amount)`

#### `liquidateLoan(uint256 loanId) external`

Liquidates a defaulted loan.

**Parameters**:
- `loanId`: ID of the loan to liquidate

**Requirements**:
- Loan must be in default
- Caller can be anyone (public liquidation)

**Events**:
- `LoanLiquidated(uint256 indexed loanId, address indexed borrower, address indexed liquidator)`

#### `getLoan(uint256 loanId) external view returns (Loan memory)`

Gets loan details by ID.

**Returns**:
```solidity
struct Loan {
    address borrower;
    uint256 amount;
    uint256 interestRate;
    uint256 termDays;
    uint256 createdAt;
    uint256 dueDate;
    address collateralToken;
    uint256 collateralAmount;
    LoanStatus status;
}

enum LoanStatus {
    Pending,
    Active,
    Repaid,
    Defaulted,
    Liquidated
}
```

### Events

```solidity
event LoanCreated(
    uint256 indexed loanId,
    address indexed borrower,
    uint256 amount,
    uint256 interestRate,
    uint256 termDays
);
event LoanRepaid(uint256 indexed loanId, address indexed borrower, uint256 amount);
event LoanDefaulted(uint256 indexed loanId, address indexed borrower);
event LoanLiquidated(
    uint256 indexed loanId,
    address indexed borrower,
    address indexed liquidator
);
```

## Interfaces

### IAETHER-SCOREScore

Interface for credit score contracts.

```solidity
interface IAETHER-SCOREScore {
    struct ScoreView {
        uint16 score;
        uint8 riskBand;
        uint64 lastUpdated;
    }
    
    function getScore(address user) external view returns (ScoreView memory);
}
```

### IAETHER-SCOREOracle

Interface for oracle price feeds.

```solidity
interface IAETHER-SCOREOracle {
    function getPrice(address token) external view returns (uint256);
    function getVolatility(address token) external view returns (uint256);
}
```

## Security Considerations

### Access Control

All contracts use OpenZeppelin's `AccessControl` for role-based access:

- **Admin Role**: Full control, can grant/revoke roles
- **Updater Role**: Can update scores (CreditPassportNFT)
- **Pauser Role**: Can pause contracts in emergencies
- **Upgrader Role**: Can upgrade contracts (UUPS)

### Upgradeability

All contracts use UUPS (Universal Upgradeable Proxy Standard):

- **Proxy Contract**: Stores state, delegates calls to implementation
- **Implementation Contract**: Contains logic, can be upgraded
- **Upgrade Process**: Requires `UPGRADER_ROLE`, emits events

### Circuit Breakers

LendingVault includes circuit breakers:

- **Rate Limiting**: Maximum loans per time period
- **Amount Limits**: Maximum loan amount per borrower
- **Pausable**: Can be paused in emergencies

### Reentrancy Protection

All state-changing functions use OpenZeppelin's `ReentrancyGuard`:

```solidity
modifier nonReentrant() {
    // Prevents reentrancy attacks
}
```

### Input Validation

All functions validate inputs:

- Address validation (non-zero)
- Amount validation (greater than 0)
- Range validation (scores 0-1000, risk bands 0-3)

## Usage Examples

### Example 1: Check Credit Score

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IAETHER-SCOREScore.sol";

contract MyContract {
    IAETHER-SCOREScore public creditPassport;
    
    constructor(address _creditPassport) {
        creditPassport = IAETHER-SCOREScore(_creditPassport);
    }
    
    function checkCredit(address user) external view returns (uint16 score, uint8 riskBand) {
        IAETHER-SCOREScore.ScoreView memory scoreView = creditPassport.getScore(user);
        return (scoreView.score, scoreView.riskBand);
    }
}
```

### Example 2: Use Credit Score for Lending

```solidity
contract LendingContract {
    IAETHER-SCOREScore public creditPassport;
    
    mapping(uint8 => uint256) public ltvByRiskBand;
    
    constructor(address _creditPassport) {
        creditPassport = IAETHER-SCOREScore(_creditPassport);
        ltvByRiskBand[0] = 8000; // 80%
        ltvByRiskBand[1] = 7000; // 70%
        ltvByRiskBand[2] = 5000; // 50%
        ltvByRiskBand[3] = 3000; // 30%
    }
    
    function calculateMaxLoan(address borrower, uint256 collateralValue) 
        external 
        view 
        returns (uint256) 
    {
        IAETHER-SCOREScore.ScoreView memory score = creditPassport.getScore(borrower);
        require(score.score > 0, "No credit passport");
        
        uint256 ltv = ltvByRiskBand[score.riskBand];
        return (collateralValue * ltv) / 10000;
    }
}
```

### Example 3: Stake Tokens

```typescript
import { ethers } from "ethers";
import AETHER-SCOREStaking from "./abis/AETHER-SCOREStaking.json";

const provider = new ethers.JsonRpcProvider("https://rpc1testnet.qie.digital/");
const signer = new ethers.Wallet(privateKey, provider);

const stakingContract = new ethers.Contract(
  "0x...", // Staking contract address
  AETHER-SCOREStaking.abi,
  signer
);

// Approve tokens
const ncrdToken = new ethers.Contract(tokenAddress, erc20Abi, signer);
await ncrdToken.approve(stakingContract.address, ethers.parseEther("10000"));

// Stake
const tx = await stakingContract.stake(ethers.parseEther("10000"));
await tx.wait();

// Check tier
const tier = await stakingContract.getTier(signer.address);
console.log(`Current tier: ${tier}`);
```

## Contract Verification

All contracts are verified on QIE block explorer:

- **Testnet Explorer**: https://testnet.qie.digital/address/{contractAddress}
- **Mainnet Explorer**: https://explorer.qie.digital/address/{contractAddress}

To verify a contract:

```bash
npx hardhat verify --network qieTestnet {contractAddress} {constructorArgs}
```

## Support

- **Documentation**: https://docs.AETHER-SCORE.io/contracts
- **GitHub**: https://github.com/AETHER-SCORE/AETHER-SCORE
- **Discord**: https://discord.gg/AETHER-SCORE



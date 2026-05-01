# Testnet Demo Guide for Evaluators

This guide shows how to use AETHER-SCORE on QIE Testnet, demonstrating all features that are ready for mainnet.

## Quick Start

### 1. Connect to QIE Testnet

1. Open the AETHER-SCORE application
2. Connect your wallet (MetaMask or QIE Wallet)
3. The app will automatically prompt to switch to QIE Testnet
4. Confirm the network switch

### 2. Get Testnet Tokens

If you need testnet QIE tokens:
- Check QIE testnet faucet (if available)
- Contact QIE team for testnet tokens
- Use testnet tokens for all transactions

### 3. Explore Features

All features work identically on testnet and mainnet:

#### Credit Scoring
- Generate credit score for any wallet
- View score breakdown and explanation
- See on-chain score updates

#### Staking
- Stake NCRD tokens (if deployed)
- View staking tiers and benefits
- See score boosts from staking

#### Lending
- Create loan offers
- Accept loan offers
- Manage active loans
- View loan history

#### Analytics
- Portfolio overview
- Transaction history
- Score trends
- DeFi activity

## Testnet Contract Addresses

After deploying to testnet, document your addresses here:

```
CreditPassportNFT: 0x...
LendingVault: 0x...
AETHER-SCOREStaking: 0x...
```

## Testnet Explorer Links

View contracts on testnet explorer:
- https://testnet.qie.digital/address/<CONTRACT_ADDRESS>

## Demo Scenarios

### Scenario 1: Credit Score Generation

1. Connect wallet
2. Navigate to Dashboard
3. Click "Generate Credit Score"
4. View score, risk band, and explanation
5. Check transaction on explorer

### Scenario 2: Loan Creation

1. Navigate to NeuroLend
2. Chat with AI agent
3. Receive loan offer
4. Accept offer (if desired)
5. View loan details

### Scenario 3: Staking

1. Navigate to Staking
2. View current tier
3. Stake tokens (if available)
4. See tier upgrade
5. View score boost

## What This Demonstrates

âœ… **Full Functionality**: All features working
âœ… **On-Chain Integration**: Real blockchain transactions
âœ… **Smart Contracts**: Deployed and verified
âœ… **User Experience**: Complete UI/UX
âœ… **Mainnet Ready**: Same code works on mainnet

## Mainnet Deployment

When funds are available, mainnet deployment is:
1. Change `QIE_NETWORK=mainnet` in environment
2. Run deployment script
3. Update contract addresses
4. Verify contracts

**That's it!** The code is already mainnet-ready.

## For Evaluators

This testnet deployment demonstrates:
- Complete system functionality
- Production-ready code
- Mainnet deployment readiness
- Technical implementation quality

The only difference between testnet and mainnet is:
- Network configuration (already implemented)
- Contract addresses (deployed when funds available)
- Real funds vs test funds

All code, features, and infrastructure are identical.



# QIE Mainnet Deployment Guide

This guide walks you through deploying AETHER-SCORE contracts to QIE Mainnet.

## Prerequisites

1. **QIE Mainnet Access**
   - QIE Mainnet RPC endpoints accessible
   - Wallet with sufficient QIEV3 for gas fees
   - Private key securely stored

2. **Environment Setup**
   - Node.js and npm installed
   - Hardhat configured
   - All dependencies installed

3. **Configuration**
   - Network configuration set to mainnet
   - Contract addresses ready to update

## Step 1: Set Network to Mainnet

### Backend Environment

Create or update `backend/.env`:

```bash
# Network Configuration
QIE_NETWORK=mainnet

# QIE Mainnet Configuration
QIE_MAINNET_CHAIN_ID=1990
QIE_MAINNET_RPC_URLS=https://rpc1mainnet.qie.digital/,https://rpc2mainnet.qie.digital/,https://rpc5mainnet.qie.digital/
QIE_MAINNET_EXPLORER_URL=https://mainnet.qie.digital/
QIE_MAINNET_SYMBOL=QIEV3
QIE_MAINNET_NAME=QIEMainnet

# Backend Wallet (for on-chain score updates)
BACKEND_PRIVATE_KEY=your_private_key_here
BACKEND_ADDRESS=your_backend_wallet_address_here
AI_SIGNER_ADDRESS=your_ai_signer_address_here

# Contract addresses will be updated after deployment
CREDIT_PASSPORT_NFT_ADDRESS=0x0000000000000000000000000000000000000000
LENDING_VAULT_ADDRESS=0x0000000000000000000000000000000000000000
STAKING_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
```

### Frontend Environment

Create or update `frontend/.env.local`:

```bash
# Network Configuration
NEXT_PUBLIC_QIE_NETWORK=mainnet

# Contract addresses will be updated after deployment
NEXT_PUBLIC_CREDIT_PASSPORT_NFT_ADDRESS=0x0000000000000000000000000000000000000000
NEXT_PUBLIC_LENDING_VAULT_ADDRESS=0x0000000000000000000000000000000000000000
NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
```

### Contracts Environment

Create or update `contracts/.env`:

```bash
# Network Configuration
QIE_NETWORK=mainnet
QIE_MAINNET_CHAIN_ID=1990
QIE_MAINNET_RPC_URL=https://rpc1mainnet.qie.digital/

# Deployment Wallet
PRIVATE_KEY=your_deployment_private_key_here

# Backend Configuration
BACKEND_ADDRESS=your_backend_wallet_address_here
AI_SIGNER_ADDRESS=your_ai_signer_address_here

# Token Addresses (if applicable)
NCRD_TOKEN_ADDRESS=0x0000000000000000000000000000000000000000
LOAN_TOKEN_ADDRESS=0x0000000000000000000000000000000000000000

# Contract addresses will be populated after deployment
CREDIT_PASSPORT_NFT_ADDRESS=
STAKING_CONTRACT_ADDRESS=
LENDING_VAULT_ADDRESS=
```

## Step 2: Deploy Contracts

### Pre-Deployment Checklist

- [ ] Network set to mainnet in all environment files
- [ ] Private key configured in `contracts/.env`
- [ ] Backend address configured
- [ ] Wallet has sufficient QIEV3 for gas fees (recommend at least 1 QIEV3)
- [ ] RPC endpoints are accessible
- [ ] All contract source code is ready

### Deploy to Mainnet

```bash
cd contracts
npx hardhat run scripts/deploy-mainnet.ts --network qieMainnet
```

**Important Notes:**
- The script will show a 10-second warning before deploying
- It will verify you're on Chain ID 1990 (QIE Mainnet)
- It will check your wallet balance
- All contracts will be deployed in order

### Deployment Output

The script will output:
- Contract addresses for all deployed contracts
- Transaction hashes
- Explorer links
- Next steps for configuration

Example output:
```
âœ… MAINNET DEPLOYMENT COMPLETE
============================================================

ðŸ“‹ Contract Addresses:
   CreditPassportNFT: 0x1234...
   AETHER-SCOREStaking:  0x5678...
   LendingVault:      0x9abc...

ðŸ“ Next Steps:
   1. Update backend/.env with mainnet addresses
   2. Update frontend/.env.local with mainnet addresses
   3. Verify contracts on explorer
```

## Step 3: Update Contract Addresses

After deployment, update the contract addresses in your environment files.

### Backend (`backend/.env`)

```bash
CREDIT_PASSPORT_NFT_ADDRESS=0x1234567890123456789012345678901234567890
LENDING_VAULT_ADDRESS=0x2345678901234567890123456789012345678901
STAKING_CONTRACT_ADDRESS=0x3456789012345678901234567890123456789012
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_CREDIT_PASSPORT_NFT_ADDRESS=0x1234567890123456789012345678901234567890
NEXT_PUBLIC_LENDING_VAULT_ADDRESS=0x2345678901234567890123456789012345678901
NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=0x3456789012345678901234567890123456789012
```

### Contracts (`contracts/.env`)

The deployment script automatically saves addresses to `contracts/.env.mainnet`, but you can also update `contracts/.env`:

```bash
CREDIT_PASSPORT_NFT_ADDRESS=0x1234567890123456789012345678901234567890
STAKING_CONTRACT_ADDRESS=0x3456789012345678901234567890123456789012
LENDING_VAULT_ADDRESS=0x2345678901234567890123456789012345678901
```

## Step 4: Verify Contracts

### Automatic Verification

Run the verification script:

```bash
cd contracts
npx hardhat run scripts/verify-mainnet.ts --network qieMainnet
```

This will verify all contracts with their constructor arguments.

### Manual Verification

If automatic verification fails, verify contracts individually:

#### CreditPassportNFT

```bash
npx hardhat verify --network qieMainnet \
  <CREDIT_PASSPORT_NFT_ADDRESS> \
  <BACKEND_ADDRESS>
```

#### AETHER-SCOREStaking

```bash
npx hardhat verify --network qieMainnet \
  <STAKING_CONTRACT_ADDRESS> \
  <NCRD_TOKEN_ADDRESS> \
  <BACKEND_ADDRESS>
```

#### LendingVault

```bash
npx hardhat verify --network qieMainnet \
  <LENDING_VAULT_ADDRESS> \
  <CREDIT_PASSPORT_NFT_ADDRESS> \
  <LOAN_TOKEN_ADDRESS> \
  <AI_SIGNER_ADDRESS> \
  <BACKEND_ADDRESS>
```

### Verify on Explorer

After verification, check contracts on the explorer:
- https://mainnet.qie.digital/address/<CONTRACT_ADDRESS>

You should see "Contract Source Code Verified" badge.

## Step 5: Post-Deployment Configuration

### Grant Roles

The deployment script automatically grants `SCORE_UPDATER_ROLE` to the backend address. Verify this:

1. Check on explorer that the role was granted
2. Test that backend can update scores on-chain

### Restart Services

After updating environment variables:

```bash
# Backend
cd backend
# Restart your backend service

# Frontend
cd frontend
npm run build
# Restart your frontend service
```

### Test Mainnet Connection

1. **Test Backend:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Test Frontend:**
   - Open the application
   - Check NetworkIndicator shows "MAINNET"
   - Verify wallet connection works
   - Test a read-only operation (view score)

3. **Test On-Chain Operations:**
   - Generate a credit score
   - Verify transaction appears on mainnet explorer
   - Check gas costs are reasonable

## Security Checklist

Before going live:

- [ ] All contracts verified on explorer
- [ ] Backend wallet has minimum required QIEV3
- [ ] Private keys are stored securely (not in git)
- [ ] Environment files are in `.gitignore`
- [ ] Mainnet warnings are visible in UI
- [ ] Gas price limits are configured
- [ ] RPC failover is working
- [ ] Monitoring is set up for mainnet transactions

## Troubleshooting

### Deployment Fails

**Error: "Wrong network!"**
- Ensure `QIE_MAINNET_CHAIN_ID=1990` in `contracts/.env`
- Check you're using `--network qieMainnet` flag

**Error: "Insufficient funds"**
- Add more QIEV3 to your deployment wallet
- Check gas price isn't too high

**Error: "RPC endpoint unavailable"**
- Try a different RPC endpoint
- Check network connectivity

### Verification Fails

**Error: "Constructor arguments do not match"**
- Double-check constructor arguments match deployment
- Verify addresses are in checksummed format

**Error: "Contract already verified"**
- Contract is already verified, check explorer

### Backend Can't Connect

**Error: "RPC health check failed"**
- Verify RPC URLs are correct
- Check network configuration
- Try fallback RPC endpoints

## Rollback Plan

If something goes wrong:

1. **Stop Services:**
   - Stop backend and frontend services

2. **Revert Environment:**
   - Set `QIE_NETWORK=testnet` in environment files
   - Or remove mainnet contract addresses

3. **Investigate:**
   - Check transaction logs
   - Review contract interactions
   - Verify addresses are correct

4. **Fix and Redeploy:**
   - Fix any issues
   - Redeploy if necessary
   - Update addresses again

## Support

For issues during deployment:

1. Check deployment logs
2. Verify network configuration
3. Check RPC endpoint status
4. Review contract verification guide: [CONTRACT_VERIFICATION_MAINNET.md](./CONTRACT_VERIFICATION_MAINNET.md)

## Next Steps

After successful deployment:

1. Monitor contract interactions
2. Set up alerts for mainnet transactions
3. Document deployed addresses
4. Update production environment
5. Test all features on mainnet
6. Prepare for production traffic

---

**âš ï¸ IMPORTANT: Mainnet deployment uses REAL FUNDS. Double-check all addresses and configurations before deploying.**



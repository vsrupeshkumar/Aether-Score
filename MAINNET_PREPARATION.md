# Mainnet Deployment Preparation Checklist

This checklist helps you prepare for QIE Mainnet deployment.

## âš ï¸ IMPORTANT: Before You Start

- [ ] You have a wallet with sufficient QIEV3 for gas fees (recommend at least 1 QIEV3)
- [ ] You have securely stored your private keys
- [ ] You understand this will use REAL FUNDS
- [ ] You have tested on testnet first
- [ ] You have reviewed all contract code

## Step 1: Environment Configuration

### Backend Configuration

Create or update `backend/.env` with:

```bash
# Network Configuration
QIE_NETWORK=mainnet

# QIE Mainnet Configuration
QIE_MAINNET_CHAIN_ID=1990
QIE_MAINNET_RPC_URLS=https://rpc1mainnet.qie.digital/,https://rpc2mainnet.qie.digital/,https://rpc5mainnet.qie.digital/
QIE_MAINNET_EXPLORER_URL=https://mainnet.qie.digital/
QIE_MAINNET_SYMBOL=QIEV3
QIE_MAINNET_NAME=QIEMainnet

# Backend Wallet (REPLACE WITH YOUR ACTUAL VALUES)
BACKEND_PRIVATE_KEY=your_actual_private_key_here
BACKEND_ADDRESS=your_backend_wallet_address_here
AI_SIGNER_ADDRESS=your_ai_signer_address_here

# Contract addresses (will be updated after deployment)
CREDIT_PASSPORT_NFT_ADDRESS=0x0000000000000000000000000000000000000000
LENDING_VAULT_ADDRESS=0x0000000000000000000000000000000000000000
STAKING_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
```

**Action Required:**
- [ ] Replace `your_actual_private_key_here` with your backend wallet private key
- [ ] Replace `your_backend_wallet_address_here` with your backend wallet address
- [ ] Replace `your_ai_signer_address_here` with your AI signer address

### Frontend Configuration

Create or update `frontend/.env.local` with:

```bash
# Network Configuration
NEXT_PUBLIC_QIE_NETWORK=mainnet

# Contract addresses (will be updated after deployment)
NEXT_PUBLIC_CREDIT_PASSPORT_NFT_ADDRESS=0x0000000000000000000000000000000000000000
NEXT_PUBLIC_LENDING_VAULT_ADDRESS=0x0000000000000000000000000000000000000000
NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
```

**Action Required:**
- [ ] File created/updated
- [ ] Addresses will be filled after deployment

### Contracts Configuration

Create or update `contracts/.env` with:

```bash
# Network Configuration
QIE_NETWORK=mainnet
QIE_MAINNET_CHAIN_ID=1990
QIE_MAINNET_RPC_URL=https://rpc1mainnet.qie.digital/

# Deployment Wallet (REPLACE WITH YOUR ACTUAL VALUES)
PRIVATE_KEY=your_deployment_private_key_here

# Backend Configuration
BACKEND_ADDRESS=your_backend_wallet_address_here
AI_SIGNER_ADDRESS=your_ai_signer_address_here

# Token Addresses (if applicable)
NCRD_TOKEN_ADDRESS=0x0000000000000000000000000000000000000000
LOAN_TOKEN_ADDRESS=0x0000000000000000000000000000000000000000
```

**Action Required:**
- [ ] Replace `your_deployment_private_key_here` with your deployment wallet private key
- [ ] Replace `your_backend_wallet_address_here` with your backend wallet address
- [ ] Replace `your_ai_signer_address_here` with your AI signer address

## Step 2: Pre-Deployment Verification

Run these checks before deploying:

### Check 1: Verify Network Configuration

```bash
cd contracts
npx hardhat run --network qieMainnet scripts/verify-mainnet.ts --dry-run
```

Expected: Should show network configuration (will fail on verification, but should show network is correct)

### Check 2: Verify Wallet Balance

```bash
cd contracts
npx hardhat run --network qieMainnet -e "console.log((await ethers.provider.getBalance(await ethers.getSigners()[0].address)).toString())"
```

Expected: Should show your wallet balance in wei

### Check 3: Verify RPC Connectivity

```bash
curl https://rpc1mainnet.qie.digital/ -X POST -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

Expected: Should return current block number

## Step 3: Deployment

When ready, run:

```bash
./scripts/deploy-mainnet.sh
```

Or manually:

```bash
cd contracts
npx hardhat run scripts/deploy-mainnet.ts --network qieMainnet
```

**During Deployment:**
- [ ] Script confirms you're on Chain ID 1990
- [ ] Script shows your wallet balance
- [ ] You confirm deployment (type "DEPLOY TO MAINNET")
- [ ] All contracts deploy successfully
- [ ] Contract addresses are saved to `contracts/.env.mainnet`

## Step 4: Update Contract Addresses

After deployment, update addresses in:

### Backend (`backend/.env`)

```bash
CREDIT_PASSPORT_NFT_ADDRESS=<address_from_deployment>
LENDING_VAULT_ADDRESS=<address_from_deployment>
STAKING_CONTRACT_ADDRESS=<address_from_deployment>
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_CREDIT_PASSPORT_NFT_ADDRESS=<address_from_deployment>
NEXT_PUBLIC_LENDING_VAULT_ADDRESS=<address_from_deployment>
NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=<address_from_deployment>
```

## Step 5: Verify Contracts

Run verification:

```bash
./scripts/verify-mainnet.sh
```

Or manually:

```bash
cd contracts
npx hardhat run scripts/verify-mainnet.ts --network qieMainnet
```

**Verification Checklist:**
- [ ] CreditPassportNFT verified
- [ ] AETHER-SCOREStaking verified (if deployed)
- [ ] LendingVault verified
- [ ] All contracts show "Contract Source Code Verified" on explorer

## Step 6: Post-Deployment

### Restart Services

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

- [ ] Backend health check works
- [ ] Frontend shows "MAINNET" in NetworkIndicator
- [ ] Wallet connection works
- [ ] Can view scores (read-only)
- [ ] Can generate score (on-chain transaction)

## Security Reminders

- [ ] `.env` files are in `.gitignore`
- [ ] Private keys are stored securely
- [ ] No private keys committed to git
- [ ] Environment files have correct permissions (600)
- [ ] Backup of private keys stored securely

## Troubleshooting

If deployment fails:
1. Check wallet has sufficient QIEV3
2. Verify RPC endpoints are accessible
3. Check network configuration is correct
4. Review deployment logs for errors

If verification fails:
1. Check constructor arguments match deployment
2. Verify compiler version matches
3. Check contract addresses are correct
4. See `docs/CONTRACT_VERIFICATION_MAINNET.md` for details

## Support

- Full deployment guide: `docs/MAINNET_DEPLOYMENT.md`
- Verification guide: `docs/CONTRACT_VERIFICATION_MAINNET.md`
- Network configuration: `backend/config/network.py`

---

**Ready to deploy?** Make sure all checkboxes above are completed, then run `./scripts/deploy-mainnet.sh`



# Staking Page Guide

## How to Use the Staking Page

### Prerequisites

1. **Deploy Contracts** (if not already deployed):
   ```bash
   cd contracts
   npx hardhat run scripts/deploy_all.ts --network qieTestnet
   ```

2. **Configure Environment Variables**:
   Add to `frontend/.env.local`:
   ```env
   NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=0xYourStakingAddress
   NEXT_PUBLIC_NCRD_TOKEN_ADDRESS=0xYourNCRDTokenAddress
   ```

3. **Get NCRD Tokens**:
   - Create NCRD token via QIEDex, OR
   - Deploy MockERC20 for testing
   - Transfer some tokens to your wallet

### Using the Staking Page

1. **Navigate to Staking Page**:
   - Go to http://localhost:3000/stake
   - Or click "Stake NCRD" from the dashboard

2. **Connect Wallet**:
   - Click "Connect Wallet" button
   - Approve connection in MetaMask/QIE Wallet
   - Ensure you're on QIE Testnet (Chain ID: 1983)

3. **View Current Status**:
   - **Current Tier**: Shows your staking tier (None, Bronze, Silver, Gold)
   - **Staked Amount**: How much NCRD you've staked
   - **NCRD Balance**: Your available NCRD tokens
   - **Score Boost**: Bonus points added to your credit score

4. **Stake Tokens**:
   - Enter amount of NCRD to stake
   - Click "Stake" button
   - Approve token spending (first time only)
   - Confirm transaction in wallet
   - Wait for confirmation

5. **Unstake Tokens**:
   - Enter amount to unstake
   - Click "Unstake" button
   - Confirm transaction in wallet
   - Wait for confirmation

### Staking Tiers

- **None (0 NCRD)**: No boost
- **Bronze (500+ NCRD)**: +50 score boost
- **Silver (2,000+ NCRD)**: +150 score boost
- **Gold (10,000+ NCRD)**: +300 score boost

### Troubleshooting

#### Error: "could not decode result data"
**Cause**: Staking contract not deployed or address not configured

**Solution**:
1. Check `NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS` is set in `.env.local`
2. Verify contract is deployed at that address
3. Ensure contract address is correct (42 characters, starts with 0x)

#### Error: "No contract found at address"
**Cause**: Contract doesn't exist at the specified address

**Solution**:
1. Deploy the AETHER-SCOREStaking contract
2. Update `.env.local` with the correct address
3. Restart frontend dev server

#### Error: "Insufficient balance"
**Cause**: Not enough NCRD tokens in wallet

**Solution**:
1. Get NCRD tokens (create via QIEDex or receive from test faucet)
2. Ensure you have enough for staking + gas fees

### Current Status

âœ… **Fixed**: Error handling for missing contracts
âœ… **Fixed**: Graceful fallback when contracts aren't deployed
âœ… **Working**: Staking page displays correctly even without contracts

The errors you saw were because the contracts aren't deployed yet. The page now handles this gracefully and shows helpful messages instead of crashing.


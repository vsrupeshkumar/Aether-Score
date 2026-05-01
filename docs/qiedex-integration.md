# QIEDex Integration Guide

QIEDex is QIE's free token creator and DEX. This guide shows how to integrate QIEDex for creating the NCRD utility token for AETHER-SCORE.

## Overview

AETHER-SCORE uses QIEDex to create the NCRD (AETHER-SCORE) utility token, which can be used for:
- Staking by dApps for integration tiers
- User rewards and fee discounts
- Governance (future)

## Creating NCRD Token via QIEDex

### Step 1: Access QIEDex

1. Go to [QIEDex](https://qiedex.qie.digital)
2. Connect your QIE Wallet
3. Navigate to "Create Token" section

### Step 2: Token Parameters

```
Token Name: AETHER-SCORE
Token Symbol: NCRD
Total Supply: 1,000,000,000 (1 billion)
Decimals: 18
```

### Step 3: Deploy Token

1. Fill in the token parameters
2. Review and confirm
3. Sign the transaction
4. Save the token contract address

### Step 4: Update Configuration

Add the NCRD token address to your environment:

```bash
# In contracts/.env
NCRD_TOKEN_ADDRESS=0x...  # Your deployed NCRD token address
```

## Integration with AETHER-SCOREStaking

Once you have the NCRD token address, you can deploy the staking contract:

```bash
cd contracts
NCRD_TOKEN_ADDRESS=0x... npm run deploy:testnet
```

The deployment script will automatically deploy `AETHER-SCOREStaking` if `NCRD_TOKEN_ADDRESS` is set.

## Using NCRD Token

### For dApps

dApps can stake NCRD tokens to unlock integration tiers:

```solidity
// In your DeFi protocol
import "./AETHER-SCOREStaking.sol";

AETHER-SCOREStaking staking = AETHER-SCOREStaking(STAKING_CONTRACT_ADDRESS);

// Stake NCRD to unlock Gold tier
uint256 amount = 10_000 * 10**18; // 10,000 NCRD
ncrdToken.approve(address(staking), amount);
staking.stake(amount);

// Check integration tier
uint8 tier = staking.integrationTier(yourProtocolAddress);
// tier: 0 = none, 1 = Bronze, 2 = Silver, 3 = Gold
```

### Integration Tiers

- **Bronze** (500 NCRD): Basic integration access
- **Silver** (2,000 NCRD): Enhanced features, priority support
- **Gold** (10,000 NCRD): Premium features, unlimited API calls

## Benefits of QIEDex Integration

1. **Free Token Creation**: No deployment costs
2. **Instant Liquidity**: Token available on QIEDex DEX
3. **Easy Trading**: Users can trade NCRD directly
4. **QIE Ecosystem**: Native integration with QIE blockchain

## Example: Creating NCRD via Script

```javascript
// Example script (not included, use QIEDex UI)
// This is just for reference

const tokenParams = {
  name: "AETHER-SCORE",
  symbol: "NCRD",
  totalSupply: ethers.parseEther("1000000000"), // 1B tokens
  decimals: 18
};

// Use QIEDex UI to create token, then save address
```

## Next Steps

1. Create NCRD token on QIEDex
2. Deploy AETHER-SCOREStaking contract with NCRD address
3. Update frontend to show staking options
4. Integrate tier system into your DeFi protocol

## Resources

- [QIEDex Website](https://qiedex.qie.digital)
- [QIE Documentation](https://docs.qie.digital/developer-docs)
- [QIE Wallet](https://qiewallet.me)



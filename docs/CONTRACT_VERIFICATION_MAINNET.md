# Contract Verification for QIE Mainnet

This guide explains how to verify AETHER-SCORE smart contracts on the QIE Mainnet explorer.

## Prerequisites

1. Contracts deployed to QIE Mainnet (Chain ID: 1990)
2. Hardhat configured with QIE mainnet network
3. Contract source code and constructor arguments
4. Compiler version and settings matching deployment

## Quick Start

### Using the Verification Script

The easiest way to verify contracts is using the provided script:

```bash
cd contracts
npx hardhat run scripts/verify-mainnet.ts --network qieMainnet
```

This script will:
- Check that you're on the correct network (Chain ID: 1990)
- Verify all deployed contracts with their constructor arguments
- Output explorer links for verified contracts

### Manual Verification

If you prefer to verify contracts manually:

#### 1. CreditPassportNFT

```bash
npx hardhat verify --network qieMainnet \
  <CREDIT_PASSPORT_NFT_ADDRESS> \
  <BACKEND_ADDRESS>
```

Example:
```bash
npx hardhat verify --network qieMainnet \
  0x1234567890123456789012345678901234567890 \
  0xabcdefabcdefabcdefabcdefabcdefabcdefabcd
```

#### 2. AETHER-SCOREStaking

```bash
npx hardhat verify --network qieMainnet \
  <STAKING_CONTRACT_ADDRESS> \
  <NCRD_TOKEN_ADDRESS> \
  <BACKEND_ADDRESS>
```

Example:
```bash
npx hardhat verify --network qieMainnet \
  0x2345678901234567890123456789012345678901 \
  0xbcdefabcdefabcdefabcdefabcdefabcdefabcde \
  0xabcdefabcdefabcdefabcdefabcdefabcdefabcd
```

#### 3. LendingVault

```bash
npx hardhat verify --network qieMainnet \
  <LENDING_VAULT_ADDRESS> \
  <CREDIT_PASSPORT_NFT_ADDRESS> \
  <LOAN_TOKEN_ADDRESS> \
  <AI_SIGNER_ADDRESS> \
  <BACKEND_ADDRESS>
```

Example:
```bash
npx hardhat verify --network qieMainnet \
  0x3456789012345678901234567890123456789012 \
  0x1234567890123456789012345678901234567890 \
  0x0000000000000000000000000000000000000000 \
  0xcdefabcdefabcdefabcdefabcdefabcdefabcdef \
  0xabcdefabcdefabcdefabcdefabcdefabcdefabcd
```

## Environment Variables

Ensure these are set in your `.env` file:

```bash
# Network Configuration
QIE_NETWORK=mainnet
QIE_MAINNET_CHAIN_ID=1990
QIE_MAINNET_RPC_URL=https://rpc1mainnet.qie.digital/

# Contract Addresses
CREDIT_PASSPORT_NFT_ADDRESS=0x...
STAKING_CONTRACT_ADDRESS=0x...
LENDING_VAULT_ADDRESS=0x...

# Deployment Configuration
BACKEND_ADDRESS=0x...
AI_SIGNER_ADDRESS=0x...
NCRD_TOKEN_ADDRESS=0x...
LOAN_TOKEN_ADDRESS=0x0000000000000000000000000000000000000000  # Native QIEV3

# Explorer API (if required)
QIE_EXPLORER_API_KEY=your_api_key_here
```

## Verification Requirements

### Compiler Settings

The contracts must be verified with the exact compiler settings used during deployment:

- **Solidity Version:** 0.8.22
- **Optimizer:** Enabled
- **Optimizer Runs:** 200
- **EVM Version:** Default (or as specified in hardhat.config.ts)

These settings are already configured in `hardhat.config.ts`:

```typescript
solidity: {
  version: "0.8.22",
  settings: {
    optimizer: {
      enabled: true,
      runs: 200,
    },
  },
}
```

### Constructor Arguments

Constructor arguments must match exactly:

1. **CreditPassportNFT:**
   - `admin`: Backend address (has SCORE_UPDATER_ROLE)

2. **AETHER-SCOREStaking:**
   - `ncrdToken`: NCRD token contract address
   - `admin`: Backend address

3. **LendingVault:**
   - `creditPassport`: CreditPassportNFT contract address
   - `loanToken`: Loan token address (0x0 for native QIEV3)
   - `aiSigner`: AI signer address (for loan offers)
   - `admin`: Backend address

## Troubleshooting

### Error: "Contract already verified"

If you see this error, the contract is already verified. You can view it on the explorer:

```
https://mainnet.qie.digital/address/<CONTRACT_ADDRESS>
```

### Error: "Constructor arguments do not match"

This means the constructor arguments provided don't match the deployed contract. Check:

1. Addresses are correct (checksummed format)
2. Order of arguments matches the constructor
3. Native token address is `0x0000000000000000000000000000000000000000` (not empty string)

### Error: "Compiler version mismatch"

Ensure the Solidity version in `hardhat.config.ts` matches the version used during deployment. The contracts use version 0.8.22.

### Error: "Network not found"

Make sure `qieMainnet` is configured in `hardhat.config.ts`:

```typescript
networks: {
  qieMainnet: {
    url: process.env.QIE_MAINNET_RPC_URL || "https://rpc1mainnet.qie.digital/",
    chainId: parseInt(process.env.QIE_MAINNET_CHAIN_ID || "1990"),
    accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
  }
}
```

### Error: "RPC endpoint unavailable"

If the RPC endpoint is down, try using a fallback:

```bash
QIE_MAINNET_RPC_URL=https://rpc2mainnet.qie.digital/ \
npx hardhat verify --network qieMainnet ...
```

Or:

```bash
QIE_MAINNET_RPC_URL=https://rpc5mainnet.qie.digital/ \
npx hardhat verify --network qieMainnet ...
```

## Verification Checklist

Before verifying, ensure:

- [ ] Contracts are deployed to QIE Mainnet (Chain ID: 1990)
- [ ] All contract addresses are correct
- [ ] Constructor arguments match deployment
- [ ] Compiler version is 0.8.22
- [ ] Optimizer settings match (enabled, 200 runs)
- [ ] RPC endpoint is accessible
- [ ] Network is configured in hardhat.config.ts

## Post-Verification

After successful verification:

1. **View on Explorer:**
   - Visit: `https://mainnet.qie.digital/address/<CONTRACT_ADDRESS>`
   - You should see "Contract Source Code Verified" badge

2. **Verify ABI:**
   - Check that the ABI matches your local ABI files
   - Functions and events should be identical

3. **Test Contract Interaction:**
   - Use the explorer's "Read Contract" and "Write Contract" tabs
   - Verify contract functions work as expected

## Additional Resources

- [QIE Mainnet Explorer](https://mainnet.qie.digital/)
- [Hardhat Verification Documentation](https://hardhat.org/hardhat-runner/plugins/nomicfoundation-hardhat-verify)
- [Contract Deployment Guide](../DEPLOYMENT.md)

## Support

If you encounter issues not covered in this guide:

1. Check the contract deployment logs for exact constructor arguments
2. Verify network configuration in `hardhat.config.ts`
3. Ensure RPC endpoints are accessible
4. Check explorer API status

For additional help, refer to the main deployment documentation or contact the development team.



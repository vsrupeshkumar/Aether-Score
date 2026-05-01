# Contract Verification Guide

This guide explains how to verify AETHER-SCORE smart contracts on the QIE block explorer.

## Overview

Contract verification allows users to:
- View contract source code on the explorer
- Verify contract functionality
- Interact with contracts through the explorer UI
- Build trust in the protocol

## Prerequisites

1. **Deployed Contracts**: Contracts must be deployed to QIE testnet or mainnet
2. **API Key**: QIE Explorer API key (if required)
3. **Contract Addresses**: Proxy and implementation addresses
4. **Constructor Arguments**: Any constructor parameters

## Verification Methods

### 1. Automatic Verification (Recommended)

Use the Hardhat verify plugin:

```bash
cd contracts
npx hardhat verify --network qieTestnet <CONTRACT_ADDRESS> [CONSTRUCTOR_ARGS]
```

### 2. Verify All Contracts

```bash
cd contracts
npm run verify:all
```

This script verifies all deployed contracts automatically.

### 3. Manual Verification

1. Go to [QIE Explorer](https://testnet.qie.digital)
2. Navigate to your contract address
3. Click "Verify and Publish"
4. Fill in:
   - Compiler version (0.8.20)
   - License (MIT)
   - Optimization enabled (Yes, 200 runs)
   - Source code (paste from contract file)
   - Constructor arguments (if any)

## Verification for Upgradeable Contracts

For UUPS upgradeable contracts, verify both:

1. **Proxy Contract**: The proxy address users interact with
2. **Implementation Contract**: The actual logic contract

### Getting Implementation Address

```bash
npx hardhat run scripts/get-implementation.ts --network qieTestnet <PROXY_ADDRESS>
```

Or use Hardhat upgrades:

```typescript
const impl = await upgrades.erc1967.getImplementationAddress(proxyAddress);
```

### Verify Implementation

```bash
npx hardhat verify --network qieTestnet <IMPLEMENTATION_ADDRESS>
```

## Contract Addresses

After deployment, save these addresses:

```bash
# CreditPassportNFTV2
CREDIT_PASSPORT_PROXY_ADDRESS=0x...
CREDIT_PASSPORT_IMPL_ADDRESS=0x...

# AETHER-SCOREStakingV2
STAKING_PROXY_ADDRESS=0x...
STAKING_IMPL_ADDRESS=0x...

# LendingVaultV2
LENDING_VAULT_PROXY_ADDRESS=0x...
LENDING_VAULT_IMPL_ADDRESS=0x...
```

## Verification Scripts

### Verify Single Contract

```bash
npx hardhat verify --network qieTestnet \
  --contract contracts/contracts/CreditPassportNFTV2.sol:CreditPassportNFTV2 \
  0x<PROXY_ADDRESS>
```

### Verify with Constructor Arguments

For non-upgradeable contracts:

```bash
npx hardhat verify --network qieTestnet \
  0x<CONTRACT_ADDRESS> \
  "arg1" "arg2" "arg3"
```

## Troubleshooting

### "Contract already verified"

This means the contract is already verified. No action needed.

### "Constructor arguments mismatch"

Double-check constructor arguments. For upgradeable contracts, use empty array `[]`.

### "Bytecode doesn't match"

- Ensure compiler version matches (0.8.20)
- Check optimization settings (enabled, 200 runs)
- Verify source code is correct

### "Network not supported"

Add custom chain to `hardhat.config.ts`:

```typescript
etherscan: {
  customChains: [{
    network: "qieTestnet",
    chainId: 1983,
    urls: {
      apiURL: "https://testnet.qie.digital/api",
      browserURL: "https://testnet.qie.digital"
    }
  }]
}
```

## CI/CD Verification

Contracts can be verified automatically in CI/CD:

```yaml
- name: Verify contracts
  run: npm run verify:all
  env:
    QIE_EXPLORER_API_KEY: ${{ secrets.QIE_EXPLORER_API_KEY }}
```

## Best Practices

1. **Verify Immediately**: Verify contracts right after deployment
2. **Verify Both**: For upgradeable contracts, verify proxy and implementation
3. **Document Addresses**: Keep a record of all deployed addresses
4. **Test Verification**: Test verification process on testnet first
5. **Automate**: Use scripts to automate verification

## Verification Checklist

- [ ] Contract deployed successfully
- [ ] Proxy address saved
- [ ] Implementation address saved
- [ ] Source code matches deployed bytecode
- [ ] Constructor arguments documented
- [ ] Verified on block explorer
- [ ] Verified implementation (if upgradeable)
- [ ] Verification documented in README

## References

- [Hardhat Verify Plugin](https://hardhat.org/hardhat-runner/plugins/nomicfoundation-hardhat-verify)
- [QIE Explorer](https://testnet.qie.digital)
- [OpenZeppelin Upgrades](https://docs.openzeppelin.com/upgrades-plugins/1.x/)



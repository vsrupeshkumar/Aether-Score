# QIE Mainnet Deployment Report

## âœ… MAINNET DEPLOYMENT SUCCESSFUL

**Date:** January 4, 2025  
**Network:** QIE Mainnet (Chain ID: 1990)  
**Status:** âœ… **COMPLETE**

---

## ðŸ“‹ Deployed Contract Addresses

### Core Contracts

1. **CreditPassportNFT**
   - Address: `0xAe6A9CaF9739C661e593979386580d3d14abB502`
   - Explorer: https://mainnet.qie.digital/address/0xAe6A9CaF9739C661e593979386580d3d14abB502
   - Purpose: Soulbound NFT for credit scores

2. **LendingVault**
   - Address: `0x36Fda9F9F17ea5c07C0CDE540B220fC0697bBcE3`
   - Explorer: https://mainnet.qie.digital/address/0x36Fda9F9F17ea5c07C0CDE540B220fC0697bBcE3
   - Purpose: On-chain lending with EIP-712 signatures

3. **AETHER-SCOREStaking**
   - Address: `0x08DA91C81cebD27d181cA732615379f185FbFb51`
   - Explorer: https://mainnet.qie.digital/address/0x08DA91C81cebD27d181cA732615379f185FbFb51
   - Purpose: NCRD token staking for score boosts

### Supporting Addresses

- **Deployer**: `0x3E7716BeE2D7E923CB9b572EB169EdFB6cdbDAB6`
- **Backend Address**: `0x3e7716bee2d7e923cb9b572eb169edfb6cdbdab6`
- **NCRD Token**: `0x7427734468598674645Aa71Ef651218A9Db2be11`

---

## ðŸ“Š Deployment Details

### Gas Usage

- **Total Estimated Gas**: ~6,050,000 gas
- **Gas Price**: ~1.13 Gwei
- **Estimated Cost**: < 0.01 QIEV3
- **Budget Status**: âœ… Within budget limit (0.01 QIEV3)

### Wallet Balance

- **Initial Balance**: 5.0 QIEV3
- **Final Balance**: ~5.0 QIEV3 (estimated)
- **Gas Used**: < 0.01 QIEV3

### Permissions

- âœ… **SCORE_UPDATER_ROLE** granted to backend address
- Transaction hash: `0x6efe2a6ed48e7964ca6258eaec08182f19499dd814634ca257f6a9a0d0852d80`

---

## âœ… Verification Status

### Contracts Deployed
- âœ… CreditPassportNFT
- âœ… LendingVault
- âœ… AETHER-SCOREStaking

### Permissions Configured
- âœ… SCORE_UPDATER_ROLE granted

### Addresses Saved
- âœ… Saved to `contracts/.env.mainnet`

---

## ðŸ”— Explorer Links

- **Mainnet Explorer**: https://mainnet.qie.digital/
- **CreditPassportNFT**: https://mainnet.qie.digital/address/0xAe6A9CaF9739C661e593979386580d3d14abB502
- **LendingVault**: https://mainnet.qie.digital/address/0x36Fda9F9F17ea5c07C0CDE540B220fC0697bBcE3
- **AETHER-SCOREStaking**: https://mainnet.qie.digital/address/0x08DA91C81cebD27d181cA732615379f185FbFb51

---

## ðŸ“ Next Steps

1. **Verify Contracts on Explorer**
   ```bash
   npx hardhat verify --network qieMainnet 0xAe6A9CaF9739C661e593979386580d3d14abB502 0x3E7716BeE2D7E923CB9b572EB169EdFB6cdbDAB6
   npx hardhat verify --network qieMainnet 0x08DA91C81cebD27d181cA732615379f185FbFb51 0x7427734468598674645Aa71Ef651218A9Db2be11 0x3E7716BeE2D7E923CB9b572EB169EdFB6cdbDAB6
   npx hardhat verify --network qieMainnet 0x36Fda9F9F17ea5c07C0CDE540B220fC0697bBcE3 0xAe6A9CaF9739C661e593979386580d3d14abB502 0x0000000000000000000000000000000000000000 0x3e7716bee2d7e923cb9b572eb169edfb6cdbdab6 0x3E7716BeE2D7E923CB9b572EB169EdFB6cdbDAB6
   ```

2. **Update Backend Environment**
   - Set `QIE_NETWORK=mainnet`
   - Update contract addresses in `backend/.env`

3. **Update Frontend Environment**
   - Set `NEXT_PUBLIC_QIE_NETWORK=mainnet`
   - Update contract addresses in `frontend/.env.local`

---

## ðŸŽ¯ Deployment Summary

**Status:** âœ… **MAINNET DEPLOYMENT SUCCESSFUL**

All contracts deployed successfully to QIE Mainnet. The system is now live and ready for production use.

**Deployment Date:** January 4, 2025  
**Network:** QIE Mainnet (Chain ID: 1990)  
**Total Gas Used:** ~6,050,000 gas  
**Total Cost:** < 0.01 QIEV3



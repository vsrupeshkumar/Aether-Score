# Mainnet Deployment Dry-Run Guide

## ðŸŽ¯ Purpose
Validate mainnet deployment readiness **WITHOUT** deploying any contracts or spending gas.

## ðŸ“‹ What the Dry-Run Validates

### 1. **Network Configuration**
- âœ… Verifies connection to QIE Mainnet (Chain ID: 1990)
- âœ… Tests RPC connectivity and responsiveness
- âœ… Retrieves current gas price
- âœ… Validates network is operational

### 2. **Environment Variables**
- âœ… Checks required variables (PRIVATE_KEY, etc.)
- âœ… Validates private key format
- âœ… Validates address formats for optional variables
- âœ… Warns about missing optional configurations

### 3. **Deployer Account**
- âœ… Validates deployer address
- âœ… Checks account balance
- âœ… Estimates deployment cost
- âœ… Verifies sufficient funds

### 4. **Contract Compilation**
- âœ… Verifies all contracts compile successfully
- âœ… Checks bytecode is generated
- âœ… Validates contract factories are available

### 5. **Deployment Simulation**
- âœ… Simulates contract deployments (gas estimation only)
- âœ… Validates constructor parameters
- âœ… Estimates gas for each contract
- âœ… **NO ACTUAL TRANSACTIONS SENT**

### 6. **Testnet Dependency Check**
- âœ… Scans for hardcoded testnet values
- âœ… Verifies no testnet chain IDs in mainnet config
- âœ… Checks for testnet RPC URLs
- âœ… Ensures clean separation

### 7. **Deployment Readiness Summary**
- âœ… Provides pass/fail summary
- âœ… Lists all warnings
- âœ… Gives final verdict

---

## ðŸš€ Running the Dry-Run

### Prerequisites
1. Set up `.env` file in `contracts/` directory with:
   ```bash
   PRIVATE_KEY=0x...
   QIE_MAINNET_RPC_URL=https://rpc1mainnet.qie.digital/
   QIE_MAINNET_CHAIN_ID=1990
   
   # Optional:
   NCRD_TOKEN_ADDRESS=0x...  # If deploying staking
   BACKEND_ADDRESS=0x...     # If granting role
   AI_SIGNER_ADDRESS=0x...   # For LendingVault
   LOAN_TOKEN_ADDRESS=0x0    # 0x0 for native QIE
   ```

2. Ensure contracts are compiled:
   ```bash
   cd contracts
   npx hardhat compile
   ```

### Execute Dry-Run

```bash
cd contracts
npx hardhat run scripts/dry-run-mainnet.ts --network qieMainnet
```

### Expected Output

```
ðŸ” AETHER-SCORE Mainnet Deployment Dry-Run
============================================================
This script validates deployment readiness WITHOUT deploying.

ðŸ“¡ [1/7] Validating Network Configuration...
âœ… PASS Network Chain ID
   Connected to QIE Mainnet (Chain ID: 1990)

âœ… PASS RPC Connectivity
   RPC is responsive. Latest block: 12345

âœ… PASS Gas Price
   Gas price: 1.00 Gwei

ðŸ” [2/7] Validating Environment Variables...
âœ… PASS Env: PRIVATE_KEY
   Private key format valid (masked: 0x1234...5678)

âœ… PASS Env: QIE_MAINNET_RPC_URL
   QIE Mainnet RPC URL is set

...

ðŸ“Š DRY-RUN SUMMARY
============================================================
âœ… Passed: 25
âŒ Failed: 0
âš ï¸  Warnings: 2

============================================================
âœ… ALL CHECKS PASSED - Ready for mainnet deployment!
   You can proceed with: npx hardhat run scripts/deploy-mainnet.ts --network qieMainnet
============================================================
```

---

## âœ… Success Criteria

### **All Critical Checks Must Pass:**
- âœ… Network Chain ID = 1990
- âœ… RPC connectivity working
- âœ… PRIVATE_KEY is set and valid
- âœ… Deployer balance â‰¥ 1.0 QIEV3
- âœ… All contracts compile
- âœ… Deployment simulation succeeds
- âœ… No testnet dependencies in mainnet config

### **Warnings Are Acceptable:**
- âš ï¸ Optional env vars not set (NCRD_TOKEN_ADDRESS, etc.)
- âš ï¸ Low balance warnings (if still sufficient)
- âš ï¸ Testnet env vars present (as long as not used)

### **Failures Must Be Fixed:**
- âŒ Wrong network
- âŒ RPC connection failed
- âŒ Missing required env vars
- âŒ Invalid address formats
- âŒ Insufficient balance
- âŒ Contract compilation errors
- âŒ Deployment simulation failures

---

## ðŸ” What Gets Checked

### Network Validation
- Chain ID verification (must be 1990)
- RPC endpoint connectivity
- Latest block retrieval
- Gas price retrieval

### Environment Variables
**Required:**
- `PRIVATE_KEY` - Deployer private key (validates format)

**Optional (but validated if set):**
- `NCRD_TOKEN_ADDRESS` - For staking deployment
- `BACKEND_ADDRESS` - For role grant
- `AI_SIGNER_ADDRESS` - For LendingVault
- `LOAN_TOKEN_ADDRESS` - Loan token (defaults to 0x0 for native)

### Contract Validation
- CreditPassportNFT compilation
- LendingVault compilation
- AETHER-SCOREStaking compilation (if token address set)

### Deployment Simulation
- Gas estimation for each contract
- Constructor parameter validation
- Transaction building (not sending)

### Testnet Dependency Check
- Hardhat config scan for testnet values
- Environment variable scan
- Network configuration validation

---

## ðŸš¨ Common Issues & Fixes

### Issue: "Wrong network! Expected 1990"
**Fix:** Ensure you're using `--network qieMainnet` flag

### Issue: "RPC connection failed"
**Fix:** 
- Check `QIE_MAINNET_RPC_URL` in `.env`
- Verify RPC endpoint is accessible
- Try alternative RPC: `https://rpc2mainnet.qie.digital/`

### Issue: "Missing required environment variable: PRIVATE_KEY"
**Fix:** Add `PRIVATE_KEY=0x...` to `contracts/.env`

### Issue: "Invalid private key format"
**Fix:** Private key must be `0x` + 64 hex characters (66 total)

### Issue: "Insufficient balance"
**Fix:** Add QIEV3 to deployer wallet (minimum 1.0 QIEV3 recommended)

### Issue: "Contract compilation failed"
**Fix:** Run `npx hardhat compile` first

---

## ðŸ“Š Interpreting Results

### âœ… All Passed
**Status:** Ready for deployment
**Action:** Proceed with actual deployment

### âš ï¸ Warnings Only
**Status:** Ready with caveats
**Action:** Review warnings, proceed if acceptable

### âŒ Failures Present
**Status:** Not ready
**Action:** Fix all failures before deploying

---

## ðŸ”’ Safety Features

1. **No Transactions Sent**
   - Only gas estimation
   - No contract deployments
   - No state changes

2. **Read-Only Operations**
   - Network queries only
   - Balance checks
   - Contract compilation checks

3. **Validation Only**
   - No actual deployment
   - No gas spent
   - Safe to run multiple times

---

## ðŸ“ Next Steps After Dry-Run

### If All Checks Pass:
1. Review the summary output
2. Verify estimated gas costs
3. Ensure sufficient balance
4. Proceed with actual deployment:
   ```bash
   npx hardhat run scripts/deploy-mainnet.ts --network qieMainnet
   ```

### If Warnings Present:
1. Review each warning
2. Decide if optional configs are needed
3. Set optional env vars if required
4. Re-run dry-run to verify

### If Failures Present:
1. Fix each failure
2. Re-run dry-run
3. Verify all checks pass
4. Then proceed with deployment

---

## ðŸŽ¯ Success Example

```
============================================================
ðŸ“Š DRY-RUN SUMMARY
============================================================
âœ… Passed: 25
âŒ Failed: 0
âš ï¸  Warnings: 1

âœ… ALL CHECKS PASSED - Ready for mainnet deployment!
   You can proceed with: npx hardhat run scripts/deploy-mainnet.ts --network qieMainnet
============================================================
```

This means:
- âœ… All critical validations passed
- âš ï¸ One optional warning (likely missing optional env var)
- âœ… Safe to proceed with deployment

---

## ðŸ”„ Re-running the Dry-Run

You can run the dry-run multiple times safely:
- No gas spent
- No transactions sent
- No state changes
- Useful for validating fixes

**Recommended:** Run dry-run after any configuration changes before actual deployment.



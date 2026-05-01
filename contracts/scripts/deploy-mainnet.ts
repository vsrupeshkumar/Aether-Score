import { ethers } from "hardhat";
import * as dotenv from "dotenv";
import { resolve } from "path";
import * as fs from "fs";

// Load environment variables
dotenv.config({ path: resolve(__dirname, "../.env") });

async function main() {
  console.log("ðŸš€ Starting AETHER-SCORE MAINNET deployment...\n");
  console.log("âš ï¸  WARNING: This will deploy to QIE MAINNET (Chain ID: 1990)");
  console.log("âš ï¸  Real funds will be used. Ensure you have reviewed all contracts.\n");

  // Safety check: require explicit confirmation
  const network = await ethers.provider.getNetwork();
  if (network.chainId !== 1990n) {
    throw new Error(
      `Wrong network! Expected QIE Mainnet (1990), got chain ID ${network.chainId}. ` +
      `Please use: npx hardhat run scripts/deploy-mainnet.ts --network qieMainnet`
    );
  }

  console.log(`ðŸ“¡ Network: ${network.name} (Chain ID: ${network.chainId})`);

  const [deployer] = await ethers.getSigners();
  const balance = await ethers.provider.getBalance(deployer.address);
  const balanceEth = ethers.formatEther(balance);

  console.log("ðŸ‘¤ Deploying with account:", deployer.address);
  console.log("ðŸ’° Account balance:", balanceEth, "QIEV3\n");

  // Enhanced balance check for mainnet
  const minBalance = 1.0; // Minimum 1 QIEV3 for safety
  if (parseFloat(balanceEth) < minBalance) {
    console.error(`âŒ Error: Insufficient balance! Required: ${minBalance} QIEV3, Available: ${balanceEth} QIEV3`);
    console.error("   Please add more QIEV3 to your deployment wallet before proceeding.");
    process.exit(1);
  } else if (parseFloat(balanceEth) < 2.0) {
    console.warn("âš ï¸  Warning: Low balance! You may need more QIEV3 for gas fees.");
    console.warn("   Recommended: At least 2 QIEV3 for safe deployment");
  }

  // Estimate total gas cost before deployment
  console.log("\nðŸ“Š Estimating deployment costs...");
  try {
    // More accurate estimates based on contract complexity
    const estimatedGas = {
      CreditPassportNFT: 1750000,  // Simple contract, minimal storage
      AETHER-SCOREStaking: 2000000,   // Medium complexity
      LendingVault: 2250000,       // Most complex contract
      GrantRole: 50000             // Simple role grant
    };
    
    // Calculate based on what will actually be deployed
    let totalEstimatedGas = estimatedGas.CreditPassportNFT + estimatedGas.LendingVault;
    const willDeployStaking = process.env.NCRD_TOKEN_ADDRESS && 
                              process.env.NCRD_TOKEN_ADDRESS !== "0x0000000000000000000000000000000000000000";
    if (willDeployStaking) {
      totalEstimatedGas += estimatedGas.AETHER-SCOREStaking;
    }
    
    const willGrantRole = process.env.BACKEND_ADDRESS && ethers.isAddress(process.env.BACKEND_ADDRESS);
    if (willGrantRole) {
      totalEstimatedGas += estimatedGas.GrantRole;
    }
    
    const gasPrice = await ethers.provider.getFeeData();
    const gasPriceGwei = gasPrice.gasPrice ? Number(ethers.formatUnits(gasPrice.gasPrice, "gwei")) : 1;
    const estimatedCost = (BigInt(totalEstimatedGas) * (gasPrice.gasPrice || ethers.parseUnits("1", "gwei"))) / ethers.parseEther("1");
    const estimatedCostFormatted = ethers.formatEther(estimatedCost);
    
    console.log(`   Contracts to deploy:`);
    console.log(`     - CreditPassportNFT: ~${estimatedGas.CreditPassportNFT.toLocaleString()} gas`);
    if (willDeployStaking) {
      console.log(`     - AETHER-SCOREStaking:  ~${estimatedGas.AETHER-SCOREStaking.toLocaleString()} gas`);
    } else {
      console.log(`     - AETHER-SCOREStaking:  SKIPPED (no NCRD_TOKEN_ADDRESS)`);
    }
    console.log(`     - LendingVault:      ~${estimatedGas.LendingVault.toLocaleString()} gas`);
    if (willGrantRole) {
      console.log(`     - Grant Role:        ~${estimatedGas.GrantRole.toLocaleString()} gas`);
    } else {
      console.log(`     - Grant Role:        SKIPPED (no BACKEND_ADDRESS)`);
    }
    console.log(`   â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€`);
    console.log(`   Total estimated gas:   ~${totalEstimatedGas.toLocaleString()} gas`);
    console.log(`   Gas price:             ${gasPriceGwei.toFixed(2)} Gwei`);
    console.log(`   Estimated cost:       ~${estimatedCostFormatted} QIEV3`);
    console.log(`   Current balance:      ${balanceEth} QIEV3`);
    console.log(`   Remaining after:      ~${(parseFloat(balanceEth) - parseFloat(estimatedCostFormatted)).toFixed(6)} QIEV3`);
    
    if (parseFloat(estimatedCostFormatted) > parseFloat(balanceEth) * 0.8) {
      console.warn("âš ï¸  Warning: Estimated cost is high relative to balance");
    } else if (parseFloat(estimatedCostFormatted) < parseFloat(balanceEth) * 0.1) {
      console.log("âœ… Estimated cost is well within budget");
    }
  } catch (error) {
    console.warn("âš ï¸  Could not estimate gas costs:", error);
  }

  // Additional confirmation for mainnet
  console.log("\nðŸ” MAINNET DEPLOYMENT CONFIRMATION");
  console.log("=".repeat(60));
  console.log("âš ï¸  WARNING: This will deploy contracts to QIE MAINNET");
  console.log("âš ï¸  This will use REAL FUNDS (QIEV3)");
  console.log("âš ï¸  All transactions are IRREVERSIBLE");
  console.log("");
  console.log("Network: QIE Mainnet (Chain ID: 1990)");
  console.log("Deployer:", deployer.address);
  console.log("Balance:", balanceEth, "QIEV3");
  console.log("");
  console.log("Press Ctrl+C to cancel, or wait 15 seconds to continue...");
  console.log("=".repeat(60));
  await new Promise(resolve => setTimeout(resolve, 15000));

  try {
    const deployedAddresses: Record<string, string> = {};

    // 1. Deploy CreditPassportNFT
    console.log("ðŸ“ [1/3] Deploying CreditPassportNFT...");
    const CreditPassportNFT = await ethers.getContractFactory("CreditPassportNFT");
    const passportNFT = await CreditPassportNFT.deploy(deployer.address);
    await passportNFT.waitForDeployment();
    const passportAddress = await passportNFT.getAddress();
    deployedAddresses.CREDIT_PASSPORT_NFT_ADDRESS = passportAddress;
    console.log("âœ… CreditPassportNFT deployed to:", passportAddress);

    // 2. Deploy AETHER-SCOREStaking (requires NCRD token address)
    console.log("\nðŸ“ [2/3] Deploying AETHER-SCOREStaking...");
    const ncrdTokenAddress = process.env.NCRD_TOKEN_ADDRESS;
    
    if (!ncrdTokenAddress || ncrdTokenAddress === "0x0000000000000000000000000000000000000000") {
      console.warn("âš ï¸  NCRD_TOKEN_ADDRESS not set. Skipping AETHER-SCOREStaking deployment.");
      console.log("   To deploy later: Set NCRD_TOKEN_ADDRESS in .env and run deploy script again.");
    } else {
      if (!ethers.isAddress(ncrdTokenAddress)) {
        throw new Error(`Invalid NCRD_TOKEN_ADDRESS: ${ncrdTokenAddress}`);
      }

      const AETHER-SCOREStaking = await ethers.getContractFactory("AETHER-SCOREStaking");
      const staking = await AETHER-SCOREStaking.deploy(ncrdTokenAddress, deployer.address);
      await staking.waitForDeployment();
      const stakingAddress = await staking.getAddress();
      deployedAddresses.STAKING_CONTRACT_ADDRESS = stakingAddress;
      console.log("âœ… AETHER-SCOREStaking deployed to:", stakingAddress);
    }

    // 3. Deploy LendingVault
    console.log("\nðŸ“ [3/3] Deploying LendingVault...");
    const backendAddress = process.env.BACKEND_ADDRESS || process.env.BACKEND_WALLET_ADDRESS;
    const aiSignerAddress = process.env.AI_SIGNER_ADDRESS || backendAddress || deployer.address;
    const loanTokenAddress = process.env.LOAN_TOKEN_ADDRESS || "0x0000000000000000000000000000000000000000"; // Native QIEV3
    
    const LendingVault = await ethers.getContractFactory("LendingVault");
    const vault = await LendingVault.deploy(
      passportAddress,
      loanTokenAddress,
      aiSignerAddress,
      deployer.address
    );
    await vault.waitForDeployment();
    const vaultAddress = await vault.getAddress();
    deployedAddresses.LENDING_VAULT_ADDRESS = vaultAddress;
    console.log("âœ… LendingVault deployed to:", vaultAddress);

    // Grant SCORE_UPDATER_ROLE to backend if address is provided
    if (backendAddress && ethers.isAddress(backendAddress)) {
      console.log("\nðŸ” Granting SCORE_UPDATER_ROLE to backend...");
      const SCORE_UPDATER_ROLE = await passportNFT.SCORE_UPDATER_ROLE();
      const tx = await passportNFT.grantRole(SCORE_UPDATER_ROLE, backendAddress);
      console.log("   Transaction hash:", tx.hash);
      await tx.wait();
      
      // Verify role
      const hasRole = await passportNFT.hasRole(SCORE_UPDATER_ROLE, backendAddress);
      if (hasRole) {
        console.log("âœ… SCORE_UPDATER_ROLE granted to:", backendAddress);
      } else {
        console.warn("âš ï¸  Role grant verification failed");
      }
    } else {
      console.log("\nâš ï¸  No BACKEND_ADDRESS set. Grant role manually using grant_updater_role.ts");
    }

    // Save addresses to .env.mainnet file
    const envMainnetPath = resolve(__dirname, "../.env.mainnet");
    let envContent = "# QIE Mainnet Contract Addresses\n";
    envContent += "# Generated by deploy-mainnet.ts\n\n";
    envContent += `QIE_NETWORK=mainnet\n`;
    envContent += `QIE_MAINNET_CHAIN_ID=1990\n`;
    envContent += `QIE_MAINNET_RPC_URL=https://rpc1mainnet.qie.digital/\n`;
    envContent += `QIE_MAINNET_EXPLORER_URL=https://mainnet.qie.digital/\n\n`;
    
    for (const [key, value] of Object.entries(deployedAddresses)) {
      envContent += `${key}=${value}\n`;
    }
    
    if (backendAddress && ethers.isAddress(backendAddress)) {
      envContent += `BACKEND_ADDRESS=${backendAddress}\n`;
    }
    if (aiSignerAddress && ethers.isAddress(aiSignerAddress)) {
      envContent += `AI_SIGNER_ADDRESS=${aiSignerAddress}\n`;
    }
    
    fs.writeFileSync(envMainnetPath, envContent);
    console.log(`\nðŸ’¾ Saved addresses to ${envMainnetPath}`);

    // Deployment Summary
    console.log("\n" + "=".repeat(60));
    console.log("âœ… MAINNET DEPLOYMENT COMPLETE");
    console.log("=".repeat(60));
    console.log("\nðŸ“‹ Contract Addresses:");
    console.log(`   CreditPassportNFT: ${passportAddress}`);
    if (deployedAddresses.STAKING_CONTRACT_ADDRESS) {
      console.log(`   AETHER-SCOREStaking:  ${deployedAddresses.STAKING_CONTRACT_ADDRESS}`);
    } else {
      console.log(`   AETHER-SCOREStaking:  NOT DEPLOYED (set NCRD_TOKEN_ADDRESS)`);
    }
    console.log(`   LendingVault:      ${vaultAddress}`);
    if (backendAddress && ethers.isAddress(backendAddress)) {
      console.log(`   Backend Address:   ${backendAddress}`);
    }
    
    console.log("\nðŸ“ Next Steps:");
    console.log("   1. Update backend/.env with mainnet addresses:");
    console.log(`      QIE_NETWORK=mainnet`);
    console.log(`      CREDIT_PASSPORT_NFT_ADDRESS=${passportAddress}`);
    if (deployedAddresses.STAKING_CONTRACT_ADDRESS) {
      console.log(`      STAKING_CONTRACT_ADDRESS=${deployedAddresses.STAKING_CONTRACT_ADDRESS}`);
    }
    console.log(`      LENDING_VAULT_ADDRESS=${vaultAddress}`);
    console.log("\n   2. Update frontend/.env.local with mainnet addresses:");
    console.log(`      NEXT_PUBLIC_QIE_NETWORK=mainnet`);
    console.log(`      NEXT_PUBLIC_CREDIT_PASSPORT_NFT_ADDRESS=${passportAddress}`);
    if (deployedAddresses.STAKING_CONTRACT_ADDRESS) {
      console.log(`      NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=${deployedAddresses.STAKING_CONTRACT_ADDRESS}`);
    }
    console.log(`      NEXT_PUBLIC_LENDING_VAULT_ADDRESS=${vaultAddress}`);
    console.log("\n   3. Verify contracts on explorer:");
    console.log(`      npx hardhat verify --network qieMainnet ${passportAddress} ${deployer.address}`);
    if (deployedAddresses.STAKING_CONTRACT_ADDRESS) {
      console.log(`      npx hardhat verify --network qieMainnet ${deployedAddresses.STAKING_CONTRACT_ADDRESS} ${ncrdTokenAddress} ${deployer.address}`);
    }
    console.log(`      npx hardhat verify --network qieMainnet ${vaultAddress} ${passportAddress} ${loanTokenAddress} ${aiSignerAddress} ${deployer.address}`);
    console.log("\n   4. View on explorer:");
    const explorerUrl = `https://mainnet.qie.digital/address/${passportAddress}`;
    console.log(`      ${explorerUrl}`);
    console.log("\n" + "=".repeat(60));

  } catch (error: any) {
    console.error("\nâŒ Mainnet deployment failed!");
    console.error("Error:", error.message);
    if (error.transaction) {
      console.error("Transaction:", error.transaction);
    }
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



import { ethers } from "hardhat";
import * as dotenv from "dotenv";
import { resolve } from "path";

// Load environment variables
dotenv.config({ path: resolve(__dirname, "../.env") });

async function main() {
  console.log("ðŸš€ Starting AETHER-SCORE full deployment...\n");

  // Check network
  const network = await ethers.provider.getNetwork();
  console.log(`ðŸ“¡ Network: ${network.name} (Chain ID: ${network.chainId})`);

  const [deployer] = await ethers.getSigners();
  const balance = await ethers.provider.getBalance(deployer.address);
  const balanceEth = ethers.formatEther(balance);

  console.log("ðŸ‘¤ Deploying with account:", deployer.address);
  console.log("ðŸ’° Account balance:", balanceEth, "QIE\n");

  if (parseFloat(balanceEth) < 0.01) {
    console.warn("âš ï¸  Warning: Low balance! You may need more QIE for gas fees.");
  }

  try {
    // 1. Deploy CreditPassportNFT
    console.log("ðŸ“ [1/3] Deploying CreditPassportNFT...");
    const CreditPassportNFT = await ethers.getContractFactory("CreditPassportNFT");
    const passportNFT = await CreditPassportNFT.deploy(deployer.address);
    await passportNFT.waitForDeployment();
    const passportAddress = await passportNFT.getAddress();
    console.log("âœ… CreditPassportNFT deployed to:", passportAddress);

    // 2. Deploy AETHER-SCOREStaking (requires NCRD token address)
    console.log("\nðŸ“ [2/3] Deploying AETHER-SCOREStaking...");
    const ncrdTokenAddress = process.env.NCRD_TOKEN_ADDRESS;
    
    if (!ncrdTokenAddress || ncrdTokenAddress === "0x0000000000000000000000000000000000000000") {
      console.warn("âš ï¸  NCRD_TOKEN_ADDRESS not set. Skipping AETHER-SCOREStaking deployment.");
      console.log("   To deploy later: Set NCRD_TOKEN_ADDRESS in .env and run deploy script again.");
      console.log("   Or create token via QIEDex and update .env");
    } else {
      if (!ethers.isAddress(ncrdTokenAddress)) {
        throw new Error(`Invalid NCRD_TOKEN_ADDRESS: ${ncrdTokenAddress}`);
      }

      const AETHER-SCOREStaking = await ethers.getContractFactory("AETHER-SCOREStaking");
      const staking = await AETHER-SCOREStaking.deploy(ncrdTokenAddress, deployer.address);
      await staking.waitForDeployment();
      const stakingAddress = await staking.getAddress();
      console.log("âœ… AETHER-SCOREStaking deployed to:", stakingAddress);
    }

    // 3. Deploy DemoLender
    console.log("\nðŸ“ [3/4] Deploying DemoLender...");
    const DemoLender = await ethers.getContractFactory("DemoLender");
    const lender = await DemoLender.deploy(passportAddress);
    await lender.waitForDeployment();
    const lenderAddress = await lender.getAddress();
    console.log("âœ… DemoLender deployed to:", lenderAddress);

    // 4. Deploy LendingVault (NeuroLend)
    console.log("\nðŸ“ [4/4] Deploying LendingVault...");
    const backendAddress = process.env.BACKEND_ADDRESS || process.env.BACKEND_WALLET_ADDRESS;
    const aiSignerAddress = process.env.AI_SIGNER_ADDRESS || backendAddress || deployer.address;
    const loanTokenAddress = process.env.LOAN_TOKEN_ADDRESS || "0x0000000000000000000000000000000000000000"; // Native QIE
    
    const LendingVault = await ethers.getContractFactory("LendingVault");
    const vault = await LendingVault.deploy(
      passportAddress,
      loanTokenAddress, // Use address(0) for native QIE
      aiSignerAddress,
      deployer.address
    );
    await vault.waitForDeployment();
    const vaultAddress = await vault.getAddress();
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

    // Deployment Summary
    console.log("\n" + "=".repeat(60));
    console.log("âœ… DEPLOYMENT COMPLETE");
    console.log("=".repeat(60));
    console.log("\nðŸ“‹ Contract Addresses:");
    console.log(`   CreditPassportNFT: ${passportAddress}`);
    if (ncrdTokenAddress && ncrdTokenAddress !== "0x0000000000000000000000000000000000000000") {
      const stakingAddress = await (await ethers.getContractFactory("AETHER-SCOREStaking")).deploy(ncrdTokenAddress, deployer.address).then(c => c.waitForDeployment().then(() => c.getAddress()));
      console.log(`   AETHER-SCOREStaking:  ${stakingAddress}`);
    } else {
      console.log(`   AETHER-SCOREStaking:  NOT DEPLOYED (set NCRD_TOKEN_ADDRESS)`);
    }
    console.log(`   DemoLender:        ${lenderAddress}`);
    console.log(`   LendingVault:      ${vaultAddress}`);
    if (backendAddress && ethers.isAddress(backendAddress)) {
      console.log(`   Backend Address:   ${backendAddress}`);
    }
    
    console.log("\nðŸ“ Next Steps:");
    console.log("   1. Add these addresses to backend/.env:");
    console.log(`      CREDIT_PASSPORT_NFT_ADDRESS=${passportAddress}`);
    if (ncrdTokenAddress && ncrdTokenAddress !== "0x0000000000000000000000000000000000000000") {
      console.log(`      STAKING_ADDRESS=<staking_address>`);
    }
    console.log(`      DEMO_LENDER_ADDRESS=${lenderAddress}`);
    console.log(`      LENDING_VAULT_ADDRESS=${vaultAddress}`);
    console.log(`      AI_SIGNER_ADDRESS=${aiSignerAddress}`);
    console.log("\n   2. Add to frontend/.env.local:");
    console.log(`      NEXT_PUBLIC_CONTRACT_ADDRESS=${passportAddress}`);
    console.log(`      NEXT_PUBLIC_STAKING_CONTRACT_ADDRESS=<staking_address>`);
    console.log(`      NEXT_PUBLIC_DEMO_LENDER_ADDRESS=${lenderAddress}`);
    console.log(`      NEXT_PUBLIC_LENDING_VAULT_ADDRESS=${vaultAddress}`);
    console.log("\n   3. View on explorer:");
    // Use network config for explorer URL
    const network = await ethers.provider.getNetwork();
    const explorerUrl = network.chainId === 1990n 
      ? `https://mainnet.qie.digital/address/${passportAddress}`
      : `https://testnet.qie.digital/address/${passportAddress}`;
    console.log(`      ${explorerUrl}`);
    console.log("\n" + "=".repeat(60));

  } catch (error: any) {
    console.error("\nâŒ Deployment failed!");
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



import { ethers } from "hardhat";

async function main() {
  console.log("ðŸš€ Starting AETHER-SCORE deployment...\n");

  // Check network
  const network = await ethers.provider.getNetwork();
  console.log(`ðŸ“¡ Network: ${network.name} (Chain ID: ${network.chainId})`);

  const [deployer] = await ethers.getSigners();
  const balance = await ethers.provider.getBalance(deployer.address);
  const balanceEth = ethers.formatEther(balance);

  console.log("ðŸ‘¤ Deploying with account:", deployer.address);
  console.log("ðŸ’° Account balance:", balanceEth, "QIE");

  // Check if balance is sufficient
  if (parseFloat(balanceEth) < 0.01) {
    console.warn("âš ï¸  Warning: Low balance! You may need more QIE for gas fees.");
    console.log("   Get testnet tokens from: https://qie.digital/faucet");
  }

  try {
    // Deploy CreditPassportNFT
    console.log("\nðŸ“ Deploying CreditPassportNFT...");
    const CreditPassportNFT = await ethers.getContractFactory("CreditPassportNFT");
    const passportNFT = await CreditPassportNFT.deploy(deployer.address);
    
    console.log("   Waiting for deployment confirmation...");
    await passportNFT.waitForDeployment();

    const passportAddress = await passportNFT.getAddress();
    console.log("âœ… CreditPassportNFT deployed to:", passportAddress);

    // Verify contract was deployed correctly
    const name = await passportNFT.name();
    const symbol = await passportNFT.symbol();
    console.log(`   Verified: ${name} (${symbol})`);

    // Get backend wallet address from env (or use deployer for now)
    const backendWalletAddress = process.env.BACKEND_WALLET_ADDRESS || deployer.address;
    
    if (backendWalletAddress !== deployer.address) {
      console.log("\nðŸ” Setting up score updater role...");
      const tx = await passportNFT.setScoreUpdater(backendWalletAddress, true);
      console.log("   Transaction hash:", tx.hash);
      await tx.wait();
      console.log("âœ… Score updater role granted to:", backendWalletAddress);
      
      // Verify role was granted
      const hasRole = await passportNFT.hasRole(
        await passportNFT.SCORE_UPDATER_ROLE(),
        backendWalletAddress
      );
      if (!hasRole) {
        throw new Error("Failed to verify score updater role");
      }
    } else {
      console.log("\nâš ï¸  Using deployer as score updater (set BACKEND_WALLET_ADDRESS in .env for production)");
      const tx = await passportNFT.setScoreUpdater(deployer.address, true);
      await tx.wait();
    }

    // Optional: Deploy staking contract if NCRD token address is provided
    let stakingAddress: string | undefined;
    if (process.env.NCRD_TOKEN_ADDRESS) {
      console.log("\nðŸ“ Deploying AETHER-SCOREStaking...");
      const ncrdAddress = process.env.NCRD_TOKEN_ADDRESS;
      
      // Validate NCRD address
      if (!ethers.isAddress(ncrdAddress)) {
        throw new Error(`Invalid NCRD_TOKEN_ADDRESS: ${ncrdAddress}`);
      }

      const AETHER-SCOREStaking = await ethers.getContractFactory("AETHER-SCOREStaking");
      const staking = await AETHER-SCOREStaking.deploy(ncrdAddress, deployer.address);
      
      console.log("   Waiting for deployment confirmation...");
      await staking.waitForDeployment();
      stakingAddress = await staking.getAddress();
      console.log("âœ… AETHER-SCOREStaking deployed to:", stakingAddress);
    } else {
      console.log("\nâ„¹ï¸  Skipping AETHER-SCOREStaking (NCRD_TOKEN_ADDRESS not set)");
      console.log("   To deploy staking: Create NCRD token on QIEDex, then set NCRD_TOKEN_ADDRESS in .env");
    }

    // Deployment Summary
    console.log("\n" + "=".repeat(60));
    console.log("âœ… DEPLOYMENT SUCCESSFUL");
    console.log("=".repeat(60));
    console.log("\nðŸ“‹ Contract Addresses:");
    console.log(`   CreditPassportNFT: ${passportAddress}`);
    console.log(`   Backend Wallet:    ${backendWalletAddress}`);
    if (stakingAddress) {
      console.log(`   AETHER-SCOREStaking:  ${stakingAddress}`);
    }
    
    console.log("\nðŸ“ Next Steps:");
    console.log("   1. Add these addresses to backend/.env:");
    console.log(`      CREDIT_PASSPORT_NFT_ADDRESS=${passportAddress}`);
    console.log(`      BACKEND_PRIVATE_KEY=your_backend_private_key`);
    console.log("\n   2. Add to frontend/.env.local:");
    console.log(`      NEXT_PUBLIC_CONTRACT_ADDRESS=${passportAddress}`);
    console.log("\n   3. View on explorer:");
    const explorerUrl = network.chainId === 1337n 
      ? `https://testnet.qie.digital/address/${passportAddress}`
      : `https://mainnet.qie.digital/address/${passportAddress}`;
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



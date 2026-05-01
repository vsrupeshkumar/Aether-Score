import { ethers } from "hardhat";
import * as dotenv from "dotenv";
import { resolve } from "path";

// Load environment variables
dotenv.config({ path: resolve(__dirname, "../.env") });

async function main() {
  console.log("🚀 Deploying CreditPassportNFT and setting up roles...\n");

  const [deployer] = await ethers.getSigners();
  console.log("👤 Deployer:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  const balanceEth = ethers.formatEther(balance);
  console.log("💰 Balance:", balanceEth, "QIE\n");

  if (parseFloat(balanceEth) < 0.01) {
    console.warn("⚠️  Warning: Low balance! You may need more QIE for gas fees.");
  }

  // Deploy CreditPassportNFT
  console.log("📝 Deploying CreditPassportNFT...");
  const CP = await ethers.getContractFactory("CreditPassportNFT");
  const cp = await CP.deploy(deployer.address);
  await cp.waitForDeployment();

  const contractAddress = await cp.getAddress();
  console.log("✅ CreditPassportNFT deployed at:", contractAddress);

  // Get backend address from env
  const backendAddress = process.env.BACKEND_ADDRESS || process.env.BACKEND_WALLET_ADDRESS;
  
  if (!backendAddress) {
    console.warn("\n⚠️  No BACKEND_ADDRESS set. Using deployer as backend.");
    console.log("   Set BACKEND_ADDRESS in .env to grant role to different address.");
    return;
  }

  if (!ethers.isAddress(backendAddress)) {
    throw new Error(`Invalid backend address: ${backendAddress}`);
  }

  // Grant SCORE_UPDATER_ROLE
  console.log(`\n🔐 Granting SCORE_UPDATER_ROLE to ${backendAddress}...`);
  const SCORE_UPDATER_ROLE = await cp.SCORE_UPDATER_ROLE();
  const tx = await cp.grantRole(SCORE_UPDATER_ROLE, backendAddress);
  console.log("   Transaction hash:", tx.hash);
  await tx.wait();
  console.log("✅ Granted SCORE_UPDATER_ROLE to:", backendAddress);

  // Verify role
  const hasRole = await cp.hasRole(SCORE_UPDATER_ROLE, backendAddress);
  if (!hasRole) {
    throw new Error("Failed to verify role grant");
  }
  console.log("✅ Role verified successfully");

  console.log("\n" + "=".repeat(60));
  console.log("✅ DEPLOYMENT COMPLETE");
  console.log("=".repeat(60));
  console.log(`\nContract Address: ${contractAddress}`);
  console.log(`Backend Address:  ${backendAddress}`);
  console.log("\n📝 Add to backend/.env:");
  console.log(`   CREDIT_PASSPORT_ADDRESS=${contractAddress}`);
  console.log(`   BACKEND_PK=your_backend_private_key`);
  console.log("\n📝 Add to frontend/.env.local:");
  console.log(`   NEXT_PUBLIC_CONTRACT_ADDRESS=${contractAddress}`);
  console.log("=".repeat(60));
}

main().catch((error) => {
  console.error("❌ Deployment failed:", error);
  process.exit(1);
});


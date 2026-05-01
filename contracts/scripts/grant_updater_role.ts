import { ethers } from "hardhat";
import * as dotenv from "dotenv";
import { resolve } from "path";

// Load environment variables
dotenv.config({ path: resolve(__dirname, "../.env") });

async function main() {
  console.log("🔐 Granting SCORE_UPDATER_ROLE to backend address...\n");

  const contractAddress = process.env.CREDIT_PASSPORT_ADDRESS || process.env.CREDIT_PASSPORT_NFT_ADDRESS;
  const backendAddress = process.env.BACKEND_ADDRESS || process.env.BACKEND_WALLET_ADDRESS;

  if (!contractAddress) {
    throw new Error("CREDIT_PASSPORT_ADDRESS or CREDIT_PASSPORT_NFT_ADDRESS must be set in .env");
  }

  if (!backendAddress) {
    throw new Error("BACKEND_ADDRESS or BACKEND_WALLET_ADDRESS must be set in .env");
  }

  if (!ethers.isAddress(contractAddress)) {
    throw new Error(`Invalid contract address: ${contractAddress}`);
  }

  if (!ethers.isAddress(backendAddress)) {
    throw new Error(`Invalid backend address: ${backendAddress}`);
  }

  console.log(`Contract: ${contractAddress}`);
  console.log(`Backend:  ${backendAddress}\n`);

  // Get provider
  const rpcUrl = process.env.QIE_TESTNET_RPC_URL || process.env.QIE_RPC_URL;
  const provider = rpcUrl 
    ? new ethers.JsonRpcProvider(rpcUrl)
    : ethers.provider;

  // Get deployer signer
  const [deployer] = await ethers.getSigners();
  console.log("Deployer:", deployer.address);

  // Load contract
  const CreditPassportNFT = await ethers.getContractFactory("CreditPassportNFT");
  const contract = CreditPassportNFT.attach(contractAddress).connect(deployer);

  // Get the role hash
  const SCORE_UPDATER_ROLE = await contract.SCORE_UPDATER_ROLE();
  console.log(`Role Hash: ${SCORE_UPDATER_ROLE}\n`);

  // Check if role already granted
  const hasRoleBefore = await contract.hasRole(SCORE_UPDATER_ROLE, backendAddress);
  if (hasRoleBefore) {
    console.log("✅ Role already granted!");
    console.log(`   Backend address ${backendAddress} already has SCORE_UPDATER_ROLE.`);
    process.exit(0);
  }

  // Grant role
  console.log("Granting role...");
  const tx = await contract.grantRole(SCORE_UPDATER_ROLE, backendAddress);
  console.log("Transaction hash:", tx.hash);
  console.log("Waiting for confirmation...");
  await tx.wait();

  // Verify role was granted
  const hasRoleAfter = await contract.hasRole(SCORE_UPDATER_ROLE, backendAddress);

  console.log("\n" + "=".repeat(60));
  if (hasRoleAfter) {
    console.log("✅ SCORE_UPDATER_ROLE: GRANTED SUCCESSFULLY");
    console.log(`   Backend address ${backendAddress} now has the role.`);
  } else {
    console.log("❌ SCORE_UPDATER_ROLE: GRANT FAILED");
    console.log(`   Verification failed - role may not have been granted.`);
    process.exit(1);
  }
  console.log("=".repeat(60));
}

main().catch((e) => {
  console.error("❌ Error:", e.message);
  process.exit(1);
});


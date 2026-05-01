import { ethers } from "hardhat";
import * as dotenv from "dotenv";
import { resolve } from "path";

// Load environment variables
dotenv.config({ path: resolve(__dirname, "../.env") });

async function main() {
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

  console.log("🔍 Checking SCORE_UPDATER_ROLE...\n");
  console.log(`Contract: ${contractAddress}`);
  console.log(`Backend:  ${backendAddress}\n`);

  // ABI for hasRole function
  const abi = [
    "function hasRole(bytes32 role, address account) view returns (bool)",
    "function SCORE_UPDATER_ROLE() view returns (bytes32)"
  ];

  // Get provider from hardhat config or use env
  const rpcUrl = process.env.QIE_TESTNET_RPC_URL || process.env.QIE_RPC_URL;
  const provider = rpcUrl 
    ? new ethers.JsonRpcProvider(rpcUrl)
    : ethers.provider;

  const contract = new ethers.Contract(contractAddress, abi, provider);

  // Get the role hash
  const SCORE_UPDATER_ROLE = await contract.SCORE_UPDATER_ROLE();
  console.log(`Role Hash: ${SCORE_UPDATER_ROLE}\n`);

  // Check if backend has the role
  const hasRole = await contract.hasRole(SCORE_UPDATER_ROLE, backendAddress);

  console.log("=".repeat(60));
  if (hasRole) {
    console.log("✅ SCORE_UPDATER_ROLE: GRANTED");
    console.log(`   Backend address ${backendAddress} has the role.`);
    console.log("\n   This satisfies QIE hackathon requirement for role-based access control.");
  } else {
    console.log("❌ SCORE_UPDATER_ROLE: NOT GRANTED");
    console.log(`   Backend address ${backendAddress} does NOT have the role.`);
    console.log("\n   To grant the role, run:");
    console.log(`   npx hardhat run scripts/grant_updater_role.ts --network qieTestnet`);
    console.log("   (or use grantRole function on the contract)");
  }
  console.log("=".repeat(60));

  process.exit(hasRole ? 0 : 1);
}

main().catch((e) => {
  console.error("❌ Error:", e.message);
  process.exit(1);
});


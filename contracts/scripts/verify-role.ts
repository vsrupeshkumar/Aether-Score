import { ethers } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const contractAddress = process.env.CREDIT_PASSPORT_NFT_ADDRESS;
  const backendAddress = process.env.BACKEND_WALLET_ADDRESS;

  if (!contractAddress) {
    console.error("❌ CREDIT_PASSPORT_NFT_ADDRESS not set in .env");
    process.exit(1);
  }

  if (!backendAddress) {
    console.error("❌ BACKEND_WALLET_ADDRESS not set in .env");
    process.exit(1);
  }

  console.log("🔍 Verifying SCORE_UPDATER_ROLE...\n");
  console.log(`Contract Address: ${contractAddress}`);
  console.log(`Backend Address: ${backendAddress}\n`);

  try {
    const CreditPassportNFT = await ethers.getContractFactory("CreditPassportNFT");
    const passportNFT = CreditPassportNFT.attach(contractAddress);

    // Get the role hash
    const SCORE_UPDATER_ROLE = await passportNFT.SCORE_UPDATER_ROLE();
    console.log(`SCORE_UPDATER_ROLE: ${SCORE_UPDATER_ROLE}\n`);

    // Check if backend address has the role
    const hasRole = await passportNFT.hasRole(SCORE_UPDATER_ROLE, backendAddress);

    if (hasRole) {
      console.log("✅ SUCCESS: Backend wallet has SCORE_UPDATER_ROLE");
      console.log(`   Address ${backendAddress} can call mintOrUpdate()\n`);
    } else {
      console.log("❌ FAILED: Backend wallet does NOT have SCORE_UPDATER_ROLE");
      console.log(`   Address ${backendAddress} cannot call mintOrUpdate()`);
      console.log("\n💡 To fix:");
      console.log("   1. Connect as admin");
      console.log("   2. Call: setScoreUpdater(backendAddress, true)");
      process.exit(1);
    }

    // Verify contract name
    const name = await passportNFT.name();
    const symbol = await passportNFT.symbol();
    console.log(`Contract: ${name} (${symbol})`);
    console.log("✅ Contract is deployed and accessible\n");

  } catch (error: any) {
    console.error("❌ Error verifying role:");
    console.error(error.message);
    if (error.message.includes("contract")) {
      console.error("\n💡 Make sure:");
      console.error("   1. Contract is deployed");
      console.error("   2. Contract address is correct");
      console.error("   3. You're connected to the correct network");
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


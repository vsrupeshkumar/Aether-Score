import { ethers } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const contractAddress = process.env.CREDIT_PASSPORT_NFT_ADDRESS;

  if (!contractAddress) {
    console.error("❌ CREDIT_PASSPORT_NFT_ADDRESS not set in .env");
    console.error("   Run: npm run deploy:testnet first");
    process.exit(1);
  }

  console.log("🔍 Verifying Contract Deployment...\n");
  console.log(`Contract Address: ${contractAddress}\n`);

  try {
    const CreditPassportNFT = await ethers.getContractFactory("CreditPassportNFT");
    const passportNFT = CreditPassportNFT.attach(contractAddress);

    // Verify contract is accessible
    const name = await passportNFT.name();
    const symbol = await passportNFT.symbol();
    console.log(`✅ Contract Name: ${name}`);
    console.log(`✅ Contract Symbol: ${symbol}`);

    // Verify admin role
    const [deployer] = await ethers.getSigners();
    const DEFAULT_ADMIN_ROLE = await passportNFT.DEFAULT_ADMIN_ROLE();
    const isAdmin = await passportNFT.hasRole(DEFAULT_ADMIN_ROLE, deployer.address);
    console.log(`✅ Admin Role: ${isAdmin ? "Set" : "Not Set"}`);

    // Check SCORE_UPDATER_ROLE
    const SCORE_UPDATER_ROLE = await passportNFT.SCORE_UPDATER_ROLE();
    const backendAddress = process.env.BACKEND_WALLET_ADDRESS;
    
    if (backendAddress) {
      const hasRole = await passportNFT.hasRole(SCORE_UPDATER_ROLE, backendAddress);
      console.log(`✅ Score Updater Role: ${hasRole ? "Granted" : "Not Granted"}`);
      if (!hasRole) {
        console.log("   ⚠️  Run: npm run verify:role to check details");
      }
    } else {
      console.log("⚠️  BACKEND_WALLET_ADDRESS not set - cannot verify role");
    }

    // Get network info
    const network = await ethers.provider.getNetwork();
    console.log(`\n📡 Network: ${network.name} (Chain ID: ${network.chainId})`);

    // Get explorer URL based on network
    const explorerUrl = network.chainId === 1990n
      ? `https://mainnet.qie.digital/address/${contractAddress}`
      : `https://testnet.qie.digital/address/${contractAddress}`;
    
    console.log(`\n🔗 Explorer: ${explorerUrl}`);

    console.log("\n✅ Deployment verification complete!");
    console.log("\n📝 Next Steps:");
    console.log("   1. Update backend/.env with CREDIT_PASSPORT_NFT_ADDRESS");
    console.log("   2. Update frontend/.env.local with NEXT_PUBLIC_CONTRACT_ADDRESS");
    console.log("   3. Run: npm run verify:role to verify SCORE_UPDATER_ROLE");

  } catch (error: any) {
    console.error("\n❌ Deployment verification failed:");
    console.error(error.message);
    
    if (error.message.includes("contract") || error.message.includes("code")) {
      console.error("\n💡 Possible issues:");
      console.error("   1. Contract not deployed at this address");
      console.error("   2. Wrong network (check QIE_TESTNET_RPC_URL)");
      console.error("   3. Contract address is incorrect");
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


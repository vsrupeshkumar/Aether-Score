import { ethers, upgrades } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const contractName = process.argv[2];
  const proxyAddress = process.argv[3];

  if (!contractName || !proxyAddress) {
    console.error("Usage: npx hardhat run scripts/upgrade-contract.ts --network <network> <ContractName> <ProxyAddress>");
    console.error("Example: npx hardhat run scripts/upgrade-contract.ts --network qieTestnet CreditPassportNFTV2 0x...");
    process.exit(1);
  }

  const [deployer] = await ethers.getSigners();
  console.log("Upgrading contract with account:", deployer.address);
  console.log("Contract:", contractName);
  console.log("Proxy address:", proxyAddress);

  // Get current implementation
  const currentImpl = await upgrades.erc1967.getImplementationAddress(proxyAddress);
  console.log("Current implementation:", currentImpl);

  // Deploy new implementation
  console.log("\nDeploying new implementation...");
  const ContractFactory = await ethers.getContractFactory(contractName);
  const upgraded = await upgrades.upgradeProxy(proxyAddress, ContractFactory);
  await upgraded.waitForDeployment();

  const newImpl = await upgrades.erc1967.getImplementationAddress(proxyAddress);
  console.log("New implementation:", newImpl);

  // Verify upgrade
  if (currentImpl === newImpl) {
    console.log("Warning: Implementation address unchanged (may be same version)");
  } else {
    console.log("Upgrade successful!");
    console.log("Proxy address (unchanged):", proxyAddress);
    console.log("Old implementation:", currentImpl);
    console.log("New implementation:", newImpl);
  }

  // Verify contract still works
  console.log("\nVerifying contract functionality...");
  try {
    // Try to read a public variable to verify contract is working
    const contract = await ethers.getContractAt(contractName, proxyAddress);
    if (contractName === "CreditPassportNFTV2") {
      const name = await contract.name();
      console.log("Contract name:", name);
    } else if (contractName === "AETHER-SCOREStakingV2") {
      const ncrd = await contract.ncrd();
      console.log("NCRD token:", ncrd);
    } else if (contractName === "LendingVaultV2") {
      const AETHER-SCORE = await contract.AETHER-SCORE();
      console.log("AETHER-SCORE address:", AETHER-SCORE);
    }
    console.log("Contract verification successful!");
  } catch (error) {
    console.error("Contract verification failed:", error);
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



import { ethers } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const contractAddress = process.argv[2];
  const roleName = process.argv[3];
  const account = process.argv[4];
  const action = process.argv[5]; // "grant" or "revoke"

  if (!contractAddress || !roleName || !account || !action) {
    console.error("Usage: npx hardhat run scripts/setup-roles.ts --network <network> <ContractAddress> <RoleName> <Account> <grant|revoke>");
    console.error("Role names: SCORE_UPDATER_ROLE, PAUSER_ROLE, UPGRADER_ROLE, CIRCUIT_BREAKER_ROLE, STAKING_ADMIN_ROLE, LENDING_ADMIN_ROLE");
    process.exit(1);
  }

  if (action !== "grant" && action !== "revoke") {
    console.error("Action must be 'grant' or 'revoke'");
    process.exit(1);
  }

  const [signer] = await ethers.getSigners();
  console.log("Using account:", signer.address);

  // Try to detect contract type
  let contract;
  let contractName = "";
  try {
    contract = await ethers.getContractAt("CreditPassportNFTV2", contractAddress);
    contractName = "CreditPassportNFTV2";
  } catch {
    try {
      contract = await ethers.getContractAt("AETHER-SCOREStakingV2", contractAddress);
      contractName = "AETHER-SCOREStakingV2";
    } catch {
      try {
        contract = await ethers.getContractAt("LendingVaultV2", contractAddress);
        contractName = "LendingVaultV2";
      } catch {
        console.error("Could not determine contract type");
        process.exit(1);
      }
    }
  }

  console.log("Contract:", contractName);
  console.log("Role:", roleName);
  console.log("Account:", account);
  console.log("Action:", action);

  // Get role hash
  let role;
  try {
    role = await contract[roleName]();
  } catch {
    console.error(`Role ${roleName} not found in contract`);
    process.exit(1);
  }

  // Check current role status
  const hasRole = await contract.hasRole(role, account);
  console.log("Current role status:", hasRole);

  if (action === "grant") {
    if (hasRole) {
      console.log("Account already has this role");
      return;
    }
    console.log("Granting role...");
    const tx = await contract.grantRole(role, account);
    await tx.wait();
    console.log("Role granted successfully");
    console.log("Transaction hash:", tx.hash);
  } else {
    if (!hasRole) {
      console.log("Account does not have this role");
      return;
    }
    console.log("Revoking role...");
    const tx = await contract.revokeRole(role, account);
    await tx.wait();
    console.log("Role revoked successfully");
    console.log("Transaction hash:", tx.hash);
  }

  // Verify
  const newHasRole = await contract.hasRole(role, account);
  console.log("New role status:", newHasRole);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



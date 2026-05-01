import { ethers } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const contractAddress = process.argv[2];
  const action = process.argv[3]; // "pause" or "unpause"

  if (!contractAddress || !action) {
    console.error("Usage: npx hardhat run scripts/pause-contract.ts --network <network> <ContractAddress> <pause|unpause>");
    process.exit(1);
  }

  if (action !== "pause" && action !== "unpause") {
    console.error("Action must be 'pause' or 'unpause'");
    process.exit(1);
  }

  const [signer] = await ethers.getSigners();
  console.log("Using account:", signer.address);

  // Try to detect contract type by checking for pause function
  let contract;
  try {
    contract = await ethers.getContractAt("CreditPassportNFTV2", contractAddress);
  } catch {
    try {
      contract = await ethers.getContractAt("AETHER-SCOREStakingV2", contractAddress);
    } catch {
      try {
        contract = await ethers.getContractAt("LendingVaultV2", contractAddress);
      } catch {
        console.error("Could not determine contract type. Please specify contract name.");
        process.exit(1);
      }
    }
  }

  // Check if paused
  const isPaused = await contract.paused();
  console.log("Current pause status:", isPaused);

  if (action === "pause") {
    if (isPaused) {
      console.log("Contract is already paused");
      return;
    }
    console.log("Pausing contract...");
    const tx = await contract.pause();
    await tx.wait();
    console.log("Contract paused successfully");
    console.log("Transaction hash:", tx.hash);
  } else {
    if (!isPaused) {
      console.log("Contract is not paused");
      return;
    }
    console.log("Unpausing contract...");
    const tx = await contract.unpause();
    await tx.wait();
    console.log("Contract unpaused successfully");
    console.log("Transaction hash:", tx.hash);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



import { run } from "hardhat";
import { ethers } from "hardhat";

/**
 * Verify contracts deployed on QIE Mainnet
 * 
 * Usage:
 *   npx hardhat run scripts/verify-mainnet.ts --network qieMainnet
 * 
 * Or verify individual contracts:
 *   npx hardhat verify --network qieMainnet <CONTRACT_ADDRESS> [CONSTRUCTOR_ARGS...]
 */

async function main() {
  console.log("ðŸ” Verifying contracts on QIE Mainnet...\n");

  const network = await ethers.provider.getNetwork();
  if (network.chainId !== 1990n) {
    throw new Error(
      `Wrong network! Expected QIE Mainnet (1990), got chain ID ${network.chainId}. ` +
      `Please use: npx hardhat run scripts/verify-mainnet.ts --network qieMainnet`
    );
  }

  // Contract addresses from environment or command line
  const passportAddress = process.env.CREDIT_PASSPORT_NFT_ADDRESS;
  const stakingAddress = process.env.STAKING_CONTRACT_ADDRESS;
  const vaultAddress = process.env.LENDING_VAULT_ADDRESS;
  const backendAddress = process.env.BACKEND_ADDRESS || process.env.BACKEND_WALLET_ADDRESS;
  const aiSignerAddress = process.env.AI_SIGNER_ADDRESS || backendAddress;
  const loanTokenAddress = process.env.LOAN_TOKEN_ADDRESS || "0x0000000000000000000000000000000000000000";
  const ncrdTokenAddress = process.env.NCRD_TOKEN_ADDRESS;

  if (!passportAddress) {
    console.error("âŒ CREDIT_PASSPORT_NFT_ADDRESS not set in environment");
    process.exit(1);
  }

  console.log("ðŸ“‹ Contract Addresses:");
  console.log(`   CreditPassportNFT: ${passportAddress}`);
  if (stakingAddress) {
    console.log(`   AETHER-SCOREStaking:  ${stakingAddress}`);
  }
  if (vaultAddress) {
    console.log(`   LendingVault:      ${vaultAddress}`);
  }
  console.log("");

  try {
    // Verify CreditPassportNFT
    console.log("ðŸ” [1/3] Verifying CreditPassportNFT...");
    if (!backendAddress) {
      console.warn("âš ï¸  BACKEND_ADDRESS not set, skipping CreditPassportNFT verification");
      console.log(`   Manual verification: npx hardhat verify --network qieMainnet ${passportAddress} ${backendAddress || "<BACKEND_ADDRESS>"}`);
    } else {
      try {
        await run("verify:verify", {
          address: passportAddress,
          constructorArguments: [backendAddress],
        });
        console.log("âœ… CreditPassportNFT verified");
      } catch (error: any) {
        if (error.message.includes("Already Verified")) {
          console.log("âœ… CreditPassportNFT already verified");
        } else {
          console.error("âŒ Failed to verify CreditPassportNFT:", error.message);
        }
      }
    }

    // Verify AETHER-SCOREStaking
    if (stakingAddress && ncrdTokenAddress) {
      console.log("\nðŸ” [2/3] Verifying AETHER-SCOREStaking...");
      if (!backendAddress) {
        console.warn("âš ï¸  BACKEND_ADDRESS not set, skipping AETHER-SCOREStaking verification");
        console.log(`   Manual verification: npx hardhat verify --network qieMainnet ${stakingAddress} ${ncrdTokenAddress} ${backendAddress || "<BACKEND_ADDRESS>"}`);
      } else {
        try {
          await run("verify:verify", {
            address: stakingAddress,
            constructorArguments: [ncrdTokenAddress, backendAddress],
          });
          console.log("âœ… AETHER-SCOREStaking verified");
        } catch (error: any) {
          if (error.message.includes("Already Verified")) {
            console.log("âœ… AETHER-SCOREStaking already verified");
          } else {
            console.error("âŒ Failed to verify AETHER-SCOREStaking:", error.message);
          }
        }
      }
    } else {
      console.log("\nâš ï¸  [2/3] Skipping AETHER-SCOREStaking (not deployed or addresses not set)");
    }

    // Verify LendingVault
    if (vaultAddress) {
      console.log("\nðŸ” [3/3] Verifying LendingVault...");
      if (!backendAddress || !aiSignerAddress) {
        console.warn("âš ï¸  BACKEND_ADDRESS or AI_SIGNER_ADDRESS not set, skipping LendingVault verification");
        console.log(`   Manual verification: npx hardhat verify --network qieMainnet ${vaultAddress} ${passportAddress} ${loanTokenAddress} ${aiSignerAddress || "<AI_SIGNER_ADDRESS>"} ${backendAddress || "<BACKEND_ADDRESS>"}`);
      } else {
        try {
          await run("verify:verify", {
            address: vaultAddress,
            constructorArguments: [passportAddress, loanTokenAddress, aiSignerAddress, backendAddress],
          });
          console.log("âœ… LendingVault verified");
        } catch (error: any) {
          if (error.message.includes("Already Verified")) {
            console.log("âœ… LendingVault already verified");
          } else {
            console.error("âŒ Failed to verify LendingVault:", error.message);
          }
        }
      }
    } else {
      console.log("\nâš ï¸  [3/3] Skipping LendingVault (not deployed or address not set)");
    }

    console.log("\n" + "=".repeat(60));
    console.log("âœ… Verification Complete");
    console.log("=".repeat(60));
    console.log("\nðŸ“ View verified contracts on explorer:");
    console.log(`   CreditPassportNFT: https://mainnet.qie.digital/address/${passportAddress}`);
    if (stakingAddress) {
      console.log(`   AETHER-SCOREStaking:  https://mainnet.qie.digital/address/${stakingAddress}`);
    }
    if (vaultAddress) {
      console.log(`   LendingVault:      https://mainnet.qie.digital/address/${vaultAddress}`);
    }
    console.log("");

  } catch (error: any) {
    console.error("\nâŒ Verification failed!");
    console.error("Error:", error.message);
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



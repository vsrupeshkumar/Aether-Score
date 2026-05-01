import { run } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const network = process.env.HARDHAT_NETWORK || "hardhat";
  console.log("Verifying contracts on network:", network);

  const contracts = [
    {
      name: "CreditPassportNFTV2",
      address: process.env.CREDIT_PASSPORT_PROXY_ADDRESS,
      constructorArgs: [],
      isProxy: true,
      implementation: process.env.CREDIT_PASSPORT_IMPL_ADDRESS
    },
    {
      name: "AETHER-SCOREStakingV2",
      address: process.env.STAKING_PROXY_ADDRESS,
      constructorArgs: [],
      isProxy: true,
      implementation: process.env.STAKING_IMPL_ADDRESS
    },
    {
      name: "LendingVaultV2",
      address: process.env.LENDING_VAULT_PROXY_ADDRESS,
      constructorArgs: [],
      isProxy: true,
      implementation: process.env.LENDING_VAULT_IMPL_ADDRESS
    }
  ];

  for (const contract of contracts) {
    if (!contract.address) {
      console.log(`Skipping ${contract.name} - address not set`);
      continue;
    }

    console.log(`\n=== Verifying ${contract.name} ===`);
    console.log("Proxy address:", contract.address);

    try {
      // Verify proxy (if supported by explorer)
      try {
        await run("verify:verify", {
          address: contract.address,
          constructorArguments: contract.constructorArgs
        });
        console.log(`âœ“ ${contract.name} proxy verified`);
      } catch (error: any) {
        if (error.message.includes("Already Verified")) {
          console.log(`âœ“ ${contract.name} proxy already verified`);
        } else {
          console.log(`âš  Could not verify proxy: ${error.message}`);
        }
      }

      // Verify implementation
      if (contract.isProxy && contract.implementation) {
        console.log("Implementation address:", contract.implementation);
        try {
          await run("verify:verify", {
            address: contract.implementation,
            constructorArguments: contract.constructorArgs
          });
          console.log(`âœ“ ${contract.name} implementation verified`);
        } catch (error: any) {
          if (error.message.includes("Already Verified")) {
            console.log(`âœ“ ${contract.name} implementation already verified`);
          } else {
            console.log(`âš  Could not verify implementation: ${error.message}`);
          }
        }
      }
    } catch (error: any) {
      console.error(`Error verifying ${contract.name}:`, error.message);
    }
  }

  console.log("\n=== Verification Complete ===");
  console.log("Note: Some contracts may need manual verification on the block explorer");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



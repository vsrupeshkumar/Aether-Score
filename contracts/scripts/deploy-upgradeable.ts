import { ethers, upgrades } from "hardhat";
import * as dotenv from "dotenv";

dotenv.config();

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await ethers.provider.getBalance(deployer.address)).toString());

  const admin = process.env.ADMIN_ADDRESS || deployer.address;
  console.log("Admin address:", admin);

  // Deploy CreditPassportNFTV2 as upgradeable
  console.log("\n=== Deploying CreditPassportNFTV2 ===");
  const CreditPassportNFTV2 = await ethers.getContractFactory("CreditPassportNFTV2");
  const creditPassport = await upgrades.deployProxy(
    CreditPassportNFTV2,
    [admin],
    { initializer: "initialize", kind: "uups" }
  );
  await creditPassport.waitForDeployment();
  const creditPassportAddress = await creditPassport.getAddress();
  console.log("CreditPassportNFTV2 Proxy deployed to:", creditPassportAddress);

  const creditPassportImpl = await upgrades.erc1967.getImplementationAddress(creditPassportAddress);
  console.log("CreditPassportNFTV2 Implementation:", creditPassportImpl);

  // Deploy AETHER-SCOREStakingV2 as upgradeable
  console.log("\n=== Deploying AETHER-SCOREStakingV2 ===");
  let ncrdToken = process.env.NCRD_TOKEN_ADDRESS || ethers.ZeroAddress;
  
  // If no NCRD token address provided, deploy a mock token
  if (ncrdToken === ethers.ZeroAddress || !ncrdToken) {
    console.log("NCRD_TOKEN_ADDRESS not set, deploying mock ERC20 token...");
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const mockToken = await MockERC20.deploy("AETHER-SCORE Token", "NCRD", 18);
    await mockToken.waitForDeployment();
    ncrdToken = await mockToken.getAddress();
    console.log("Mock NCRD Token deployed to:", ncrdToken);
  }

  const AETHER-SCOREStakingV2 = await ethers.getContractFactory("AETHER-SCOREStakingV2");
  const staking = await upgrades.deployProxy(
    AETHER-SCOREStakingV2,
    [ncrdToken, admin],
    { initializer: "initialize", kind: "uups" }
  );
  await staking.waitForDeployment();
  const stakingAddress = await staking.getAddress();
  console.log("AETHER-SCOREStakingV2 Proxy deployed to:", stakingAddress);

  const stakingImpl = await upgrades.erc1967.getImplementationAddress(stakingAddress);
  console.log("AETHER-SCOREStakingV2 Implementation:", stakingImpl);

  // Deploy LendingVaultV2 as upgradeable
  console.log("\n=== Deploying LendingVaultV2 ===");
  const AETHER-SCOREAddress = creditPassportAddress; // Use CreditPassportNFT as AETHER-SCORE
  const loanToken = process.env.LOAN_TOKEN_ADDRESS || ethers.ZeroAddress;
  const aiSigner = process.env.AI_SIGNER_ADDRESS || deployer.address;

  const LendingVaultV2 = await ethers.getContractFactory("LendingVaultV2");
  const lendingVault = await upgrades.deployProxy(
    LendingVaultV2,
    [AETHER-SCOREAddress, loanToken, aiSigner, admin],
    { initializer: "initialize", kind: "uups" }
  );
  await lendingVault.waitForDeployment();
  const lendingVaultAddress = await lendingVault.getAddress();
  console.log("LendingVaultV2 Proxy deployed to:", lendingVaultAddress);

  const lendingVaultImpl = await upgrades.erc1967.getImplementationAddress(lendingVaultAddress);
  console.log("LendingVaultV2 Implementation:", lendingVaultImpl);

  // Setup roles
  console.log("\n=== Setting up roles ===");
  
  // Grant SCORE_UPDATER_ROLE to backend
  const backendAddress = process.env.BACKEND_ADDRESS || deployer.address;
  const SCORE_UPDATER_ROLE = await creditPassport.SCORE_UPDATER_ROLE();
  const tx1 = await creditPassport.grantRole(SCORE_UPDATER_ROLE, backendAddress);
  await tx1.wait();
  console.log("Granted SCORE_UPDATER_ROLE to:", backendAddress);

  // Summary
  console.log("\n=== Deployment Summary ===");
  console.log("CreditPassportNFTV2 Proxy:", creditPassportAddress);
  console.log("CreditPassportNFTV2 Impl:", creditPassportImpl);
  console.log("AETHER-SCOREStakingV2 Proxy:", stakingAddress);
  console.log("AETHER-SCOREStakingV2 Impl:", stakingImpl);
  console.log("LendingVaultV2 Proxy:", lendingVaultAddress);
  console.log("LendingVaultV2 Impl:", lendingVaultImpl);
  console.log("\nSave these addresses for verification and upgrades!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });



import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { CreditPassportNFTV2, AETHER-SCOREStakingV2, LendingVaultV2 } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("Pausable Contracts", function () {
  let admin: HardhatEthersSigner;
  let pauser: HardhatEthersSigner;
  let user: HardhatEthersSigner;
  let scoreUpdater: HardhatEthersSigner;

  beforeEach(async function () {
    [admin, pauser, user, scoreUpdater] = await ethers.getSigners();
  });

  describe("CreditPassportNFTV2 Pausable", function () {
    let creditPassport: CreditPassportNFTV2;

    beforeEach(async function () {
      const CreditPassportNFTV2Factory = await ethers.getContractFactory("CreditPassportNFTV2");
      creditPassport = await upgrades.deployProxy(
        CreditPassportNFTV2Factory,
        [admin.address],
        { initializer: "initialize", kind: "uups" }
      ) as unknown as CreditPassportNFTV2;

      const SCORE_UPDATER_ROLE = await creditPassport.SCORE_UPDATER_ROLE();
      await creditPassport.grantRole(SCORE_UPDATER_ROLE, scoreUpdater.address);

      const PAUSER_ROLE = await creditPassport.PAUSER_ROLE();
      await creditPassport.grantRole(PAUSER_ROLE, pauser.address);
    });

    it("Should start unpaused", async function () {
      expect(await creditPassport.paused()).to.be.false;
    });

    it("Should pause and unpause", async function () {
      await creditPassport.connect(pauser).pause();
      expect(await creditPassport.paused()).to.be.true;

      await creditPassport.connect(pauser).unpause();
      expect(await creditPassport.paused()).to.be.false;
    });

    it("Should prevent operations when paused", async function () {
      await creditPassport.connect(pauser).pause();
      await expect(
        creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750, 2)
      ).to.be.revertedWithCustomError(creditPassport, "EnforcedPause");
    });

    it("Should only allow pauser role to pause", async function () {
      await expect(
        creditPassport.connect(user).pause()
      ).to.be.reverted;
    });
  });

  describe("AETHER-SCOREStakingV2 Pausable", function () {
    let staking: AETHER-SCOREStakingV2;
    let mockToken: any;

    beforeEach(async function () {
      // Deploy mock ERC20 token
      const MockERC20 = await ethers.getContractFactory("MockERC20");
      mockToken = await MockERC20.deploy("Test Token", "TEST", 18);
      await mockToken.waitForDeployment();
      
      // Deploy staking contract
      const AETHER-SCOREStakingV2Factory = await ethers.getContractFactory("AETHER-SCOREStakingV2");
      staking = await upgrades.deployProxy(
        AETHER-SCOREStakingV2Factory,
        [await mockToken.getAddress(), admin.address],
        { initializer: "initialize", kind: "uups" }
      ) as unknown as AETHER-SCOREStakingV2;

      const PAUSER_ROLE = await staking.PAUSER_ROLE();
      await staking.grantRole(PAUSER_ROLE, pauser.address);

      // Mint tokens to user and approve staking contract
      await mockToken.mint(user.address, ethers.parseEther("1000"));
      await mockToken.connect(user).approve(await staking.getAddress(), ethers.MaxUint256);
    });

    it("Should prevent staking when paused", async function () {
      await staking.connect(pauser).pause();
      await expect(
        staking.connect(user).stake(ethers.parseEther("100"))
      ).to.be.revertedWithCustomError(staking, "EnforcedPause");
    });

    it("Should prevent unstaking when paused", async function () {
      await staking.connect(user).stake(ethers.parseEther("100"));
      await staking.connect(pauser).pause();
      await expect(
        staking.connect(user).unstake(ethers.parseEther("50"))
      ).to.be.revertedWithCustomError(staking, "EnforcedPause");
    });
  });
});



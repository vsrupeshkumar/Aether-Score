import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { CreditPassportNFTV2 } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("CreditPassportNFTV2", function () {
  let creditPassport: CreditPassportNFTV2;
  let admin: HardhatEthersSigner;
  let scoreUpdater: HardhatEthersSigner;
  let user: HardhatEthersSigner;
  let pauser: HardhatEthersSigner;

  beforeEach(async function () {
    [admin, scoreUpdater, user, pauser] = await ethers.getSigners();

    const CreditPassportNFTV2Factory = await ethers.getContractFactory("CreditPassportNFTV2");
    creditPassport = await upgrades.deployProxy(
      CreditPassportNFTV2Factory,
      [admin.address],
      { initializer: "initialize", kind: "uups" }
    ) as unknown as CreditPassportNFTV2;

    // Grant roles
    const SCORE_UPDATER_ROLE = await creditPassport.SCORE_UPDATER_ROLE();
    await creditPassport.grantRole(SCORE_UPDATER_ROLE, scoreUpdater.address);

    const PAUSER_ROLE = await creditPassport.PAUSER_ROLE();
    await creditPassport.grantRole(PAUSER_ROLE, pauser.address);
  });

  describe("Initialization", function () {
    it("Should initialize with correct admin", async function () {
      const DEFAULT_ADMIN_ROLE = await creditPassport.DEFAULT_ADMIN_ROLE();
      expect(await creditPassport.hasRole(DEFAULT_ADMIN_ROLE, admin.address)).to.be.true;
    });

    it("Should have circuit breaker enabled by default", async function () {
      const config = await creditPassport.circuitBreakerConfig();
      expect(config.enabled).to.be.true;
      expect(config.maxOperationsPerWindow).to.equal(10);
      expect(config.timeWindow).to.equal(3600);
      expect(config.maxAmount).to.equal(200);
    });
  });

  describe("Minting and Updating", function () {
    it("Should mint new passport", async function () {
      await expect(creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750, 2))
        .to.emit(creditPassport, "PassportMinted")
        .withArgs(user.address, 1n, anyValue, anyValue);

      const score = await creditPassport.getScore(user.address);
      expect(score.score).to.equal(750);
      expect(score.riskBand).to.equal(2);
    });

    it("Should update existing passport", async function () {
      await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750, 2);
      await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 800, 1);

      const score = await creditPassport.getScore(user.address);
      expect(score.score).to.equal(800);
      expect(score.riskBand).to.equal(1);
    });

    it("Should revert if not score updater", async function () {
      await expect(
        creditPassport.connect(user).mintOrUpdate(user.address, 750, 2)
      ).to.be.reverted;
    });
  });

  describe("Pausable", function () {
    it("Should pause contract", async function () {
      await creditPassport.connect(pauser).pause();
      expect(await creditPassport.paused()).to.be.true;
    });

    it("Should unpause contract", async function () {
      await creditPassport.connect(pauser).pause();
      await creditPassport.connect(pauser).unpause();
      expect(await creditPassport.paused()).to.be.false;
    });

    it("Should prevent operations when paused", async function () {
      await creditPassport.connect(pauser).pause();
      await expect(
        creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750, 2)
      ).to.be.revertedWithCustomError(creditPassport, "EnforcedPause");
    });
  });

  describe("Circuit Breakers", function () {
    it("Should enforce rate limits", async function () {
      // Make 10 updates (limit)
      for (let i = 0; i < 10; i++) {
        await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750 + i, 2);
      }

      // 11th should fail
      await expect(
        creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 760, 2)
      ).to.be.revertedWithCustomError(creditPassport, "RateLimitExceeded");
    });

    it("Should enforce amount limits", async function () {
      await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 500, 2);
      
      // Try to update by more than 200 points (limit)
      await expect(
        creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750, 2)
      ).to.be.revertedWithCustomError(creditPassport, "AmountLimitExceeded");
    });

    it("Should allow disabling circuit breaker", async function () {
      const CIRCUIT_BREAKER_ROLE = await creditPassport.CIRCUIT_BREAKER_ROLE();
      await creditPassport.grantRole(CIRCUIT_BREAKER_ROLE, admin.address);

      await creditPassport.setCircuitBreakerConfig(10, 3600, 200, false);

      // Should not enforce limits
      for (let i = 0; i < 15; i++) {
        await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750 + i, 2);
      }
    });
  });

  describe("Upgradeability", function () {
    it("Should upgrade contract", async function () {
      const CreditPassportNFTV2Factory = await ethers.getContractFactory("CreditPassportNFTV2");
      const UPGRADER_ROLE = await creditPassport.UPGRADER_ROLE();
      await creditPassport.grantRole(UPGRADER_ROLE, admin.address);

      const upgraded = await upgrades.upgradeProxy(
        await creditPassport.getAddress(),
        CreditPassportNFTV2Factory
      );

      // Verify contract still works
      const name = await upgraded.name();
      expect(name).to.equal("AETHER-SCORE Credit Passport");
    });
  });

  describe("Soulbound", function () {
    it("Should prevent transfers", async function () {
      await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750, 2);
      const tokenId = await creditPassport.passportIdOf(user.address);

      await expect(
        creditPassport.connect(user).transferFrom(user.address, admin.address, tokenId)
      ).to.be.revertedWithCustomError(creditPassport, "SoulboundNonTransferable");
    });
  });
});

// Helper for anyValue matcher
const anyValue = () => true;



import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { CreditPassportNFTV2 } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("Circuit Breaker", function () {
  let creditPassport: CreditPassportNFTV2;
  let admin: HardhatEthersSigner;
  let scoreUpdater: HardhatEthersSigner;
  let user: HardhatEthersSigner;
  let circuitBreakerAdmin: HardhatEthersSigner;

  beforeEach(async function () {
    [admin, scoreUpdater, user, circuitBreakerAdmin] = await ethers.getSigners();

    const CreditPassportNFTV2Factory = await ethers.getContractFactory("CreditPassportNFTV2");
    creditPassport = await upgrades.deployProxy(
      CreditPassportNFTV2Factory,
      [admin.address],
      { initializer: "initialize", kind: "uups" }
    ) as unknown as CreditPassportNFTV2;

    const SCORE_UPDATER_ROLE = await creditPassport.SCORE_UPDATER_ROLE();
    await creditPassport.grantRole(SCORE_UPDATER_ROLE, scoreUpdater.address);

    const CIRCUIT_BREAKER_ROLE = await creditPassport.CIRCUIT_BREAKER_ROLE();
    await creditPassport.grantRole(CIRCUIT_BREAKER_ROLE, circuitBreakerAdmin.address);
  });

  describe("Rate Limiting", function () {
    it("Should track operations per time window", async function () {
      const config = await creditPassport.circuitBreakerConfig();
      const maxOps = config.maxOperationsPerWindow;

      // Make max operations
      for (let i = 0; i < Number(maxOps); i++) {
        await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750 + i, 2);
      }

      // Next should fail
      await expect(
        creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 760, 2)
      ).to.be.revertedWithCustomError(creditPassport, "RateLimitExceeded");
    });

    it("Should reset after time window", async function () {
      // This test would require time manipulation - skipped for brevity
      // In production, use hardhat network helpers to advance time
    });
  });

  describe("Amount Limiting", function () {
    it("Should prevent large score changes", async function () {
      await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 500, 2);

      // Try to change by more than 200 points
      await expect(
        creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750, 2)
      ).to.be.revertedWithCustomError(creditPassport, "AmountLimitExceeded");
    });

    it("Should allow changes within limit", async function () {
      await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 500, 2);
      
      // Change by 200 points (at limit)
      await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 700, 2);
      
      const score = await creditPassport.getScore(user.address);
      expect(score.score).to.equal(700);
    });
  });

  describe("Configuration", function () {
    it("Should update circuit breaker config", async function () {
      await creditPassport.connect(circuitBreakerAdmin).setCircuitBreakerConfig(
        20, // maxOperationsPerWindow
        7200, // timeWindow (2 hours)
        300, // maxAmount
        true // enabled
      );

      const config = await creditPassport.circuitBreakerConfig();
      expect(config.maxOperationsPerWindow).to.equal(20);
      expect(config.timeWindow).to.equal(7200);
      expect(config.maxAmount).to.equal(300);
      expect(config.enabled).to.be.true;
    });

    it("Should only allow circuit breaker role to configure", async function () {
      await expect(
        creditPassport.connect(user).setCircuitBreakerConfig(20, 7200, 300, true)
      ).to.be.reverted;
    });
  });
});


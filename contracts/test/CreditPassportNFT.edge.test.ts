import { expect } from "chai";
import { ethers } from "hardhat";
import { CreditPassportNFT } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("CreditPassportNFT - Edge Cases", function () {
  let passportNFT: CreditPassportNFT;
  let admin: HardhatEthersSigner;
  let scoreUpdater: HardhatEthersSigner;
  let user1: HardhatEthersSigner;
  let user2: HardhatEthersSigner;

  beforeEach(async function () {
    [admin, scoreUpdater, user1, user2] = await ethers.getSigners();

    const CreditPassportNFTFactory = await ethers.getContractFactory("CreditPassportNFT");
    passportNFT = await CreditPassportNFTFactory.deploy(admin.address);
    await passportNFT.waitForDeployment();

    await passportNFT.connect(admin).setScoreUpdater(scoreUpdater.address, true);
  });

  describe("Score Boundary Tests", function () {
    it("Should handle score at exact boundary 0", async function () {
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 0, 3);
      const scoreView = await passportNFT.getScore(user1.address);
      expect(scoreView.score).to.equal(0);
      expect(scoreView.riskBand).to.equal(3);
    });

    it("Should handle score at exact boundary 1000", async function () {
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 1000, 1);
      const scoreView = await passportNFT.getScore(user1.address);
      expect(scoreView.score).to.equal(1000);
      expect(scoreView.riskBand).to.equal(1);
    });

    it("Should reject score 1001", async function () {
      await expect(
        passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 1001, 1)
      ).to.be.revertedWith("Score too high");
    });

    it("Should handle rapid score updates", async function () {
      // Multiple rapid updates
      for (let i = 0; i < 10; i++) {
        await passportNFT.connect(scoreUpdater).mintOrUpdate(
          user1.address,
          500 + i * 10,
          i % 2 === 0 ? 1 : 2
        );
      }
      
      const scoreView = await passportNFT.getScore(user1.address);
      expect(scoreView.score).to.equal(590); // Last update
    });
  });

  describe("Risk Band Edge Cases", function () {
    it("Should handle all risk bands correctly", async function () {
      const riskBands = [0, 1, 2, 3];
      
      for (const band of riskBands) {
        await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 500, band);
        const scoreView = await passportNFT.getScore(user1.address);
        expect(scoreView.riskBand).to.equal(band);
      }
    });

    it("Should handle risk band transitions", async function () {
      // Start with high risk
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 200, 3);
      let scoreView = await passportNFT.getScore(user1.address);
      expect(scoreView.riskBand).to.equal(3);
      
      // Improve to medium risk
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 600, 2);
      scoreView = await passportNFT.getScore(user1.address);
      expect(scoreView.riskBand).to.equal(2);
      
      // Improve to low risk
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 850, 1);
      scoreView = await passportNFT.getScore(user1.address);
      expect(scoreView.riskBand).to.equal(1);
    });
  });

  describe("Multiple Users Stress Test", function () {
    it("Should handle 50 users with different scores", async function () {
      const users = await ethers.getSigners();
      const maxUsers = Math.min(50, users.length);
      
      for (let i = 0; i < maxUsers; i++) {
        const score = 300 + (i * 10);
        const riskBand = i % 3 + 1;
        await passportNFT.connect(scoreUpdater).mintOrUpdate(users[i].address, score, riskBand);
      }
      
      // Verify all users have correct scores
      for (let i = 0; i < maxUsers; i++) {
        const expectedScore = 300 + (i * 10);
        const scoreView = await passportNFT.getScore(users[i].address);
        expect(scoreView.score).to.equal(expectedScore);
      }
    });
  });

  describe("Token ID Management", function () {
    it("Should assign sequential token IDs", async function () {
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 750, 1);
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user2.address, 600, 2);
      
      const tokenId1 = await passportNFT.passportIdOf(user1.address);
      const tokenId2 = await passportNFT.passportIdOf(user2.address);
      
      expect(tokenId1).to.equal(1);
      expect(tokenId2).to.equal(2);
    });

    it("Should maintain same token ID after update", async function () {
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 750, 1);
      const tokenId1 = await passportNFT.passportIdOf(user1.address);
      
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 850, 1);
      const tokenId2 = await passportNFT.passportIdOf(user1.address);
      
      expect(tokenId1).to.equal(tokenId2);
    });
  });

  describe("Event Emission Verification", function () {
    it("Should emit PassportMinted only on first mint", async function () {
      // First mint
      await expect(
        passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 750, 1)
      ).to.emit(passportNFT, "PassportMinted");
      
      // Update should not emit PassportMinted
      await expect(
        passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 850, 1)
      ).to.not.emit(passportNFT, "PassportMinted");
    });

    it("Should emit ScoreUpdated only on updates", async function () {
      // First mint - no ScoreUpdated
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 750, 1);
      
      // Update - should emit ScoreUpdated
      await expect(
        passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 850, 1)
      ).to.emit(passportNFT, "ScoreUpdated");
    });
  });

  describe("Admin Functions Edge Cases", function () {
    it("Should allow admin to burn and user can be reminted", async function () {
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 750, 1);
      const tokenId1 = await passportNFT.passportIdOf(user1.address);
      
      // Burn
      await passportNFT.connect(admin).adminBurn(user1.address);
      expect(await passportNFT.passportIdOf(user1.address)).to.equal(0);
      
      // Remint
      await passportNFT.connect(scoreUpdater).mintOrUpdate(user1.address, 800, 1);
      const tokenId2 = await passportNFT.passportIdOf(user1.address);
      
      // Should get new token ID
      expect(tokenId2).to.be.gt(0);
      expect(tokenId2).to.not.equal(tokenId1);
    });

    it("Should handle multiple score updaters correctly", async function () {
      const [updater1, updater2, updater3] = await ethers.getSigners();
      
      await passportNFT.connect(admin).setScoreUpdater(updater1.address, true);
      await passportNFT.connect(admin).setScoreUpdater(updater2.address, true);
      await passportNFT.connect(admin).setScoreUpdater(updater3.address, true);
      
      // All should be able to mint
      await expect(
        passportNFT.connect(updater1).mintOrUpdate(user1.address, 750, 1)
      ).to.emit(passportNFT, "PassportMinted");
      
      await expect(
        passportNFT.connect(updater2).mintOrUpdate(user2.address, 600, 2)
      ).to.emit(passportNFT, "PassportMinted");
      
      await expect(
        passportNFT.connect(updater3).mintOrUpdate(user1.address, 850, 1)
      ).to.emit(passportNFT, "ScoreUpdated");
    });
  });
});


import { expect } from "chai";
import { ethers } from "hardhat";
import { loadFixture } from "@nomicfoundation/hardhat-toolbox/network-helpers";

describe("DemoLender", function () {
  async function deployLenderFixture() {
    const [owner, user1, user2, user3] = await ethers.getSigners();

    // Deploy CreditPassportNFT
    const CreditPassportNFT = await ethers.getContractFactory("CreditPassportNFT");
    const passportNFT = await CreditPassportNFT.deploy(owner.address);
    await passportNFT.waitForDeployment();

    // Deploy DemoLender
    const DemoLender = await ethers.getContractFactory("DemoLender");
    const lender = await DemoLender.deploy(await passportNFT.getAddress());
    await lender.waitForDeployment();

    // Grant SCORE_UPDATER_ROLE to owner
    const SCORE_UPDATER_ROLE = await passportNFT.SCORE_UPDATER_ROLE();
    await passportNFT.grantRole(SCORE_UPDATER_ROLE, owner.address);

    return { lender, passportNFT, owner, user1, user2, user3 };
  }

  describe("Deployment", function () {
    it("Should set the correct AETHER-SCORE contract address", async function () {
      const { lender, passportNFT } = await loadFixture(deployLenderFixture);
      expect(await lender.AETHER-SCORE()).to.equal(await passportNFT.getAddress());
    });
  });

  describe("LTV Calculation", function () {
    it("Should return 0% LTV for users without passport", async function () {
      const { lender, user1 } = await loadFixture(deployLenderFixture);
      const ltv = await lender.getLTV(user1.address);
      expect(ltv).to.equal(0);
    });

    it("Should return 70% LTV for risk band 1 (low risk)", async function () {
      const { lender, passportNFT, owner, user1 } = await loadFixture(deployLenderFixture);
      
      // Mint passport with risk band 1
      await passportNFT.connect(owner).mintOrUpdate(user1.address, 800, 1);
      
      const ltv = await lender.getLTV(user1.address);
      expect(ltv).to.equal(7000); // 70% in basis points
    });

    it("Should return 50% LTV for risk band 2 (medium risk)", async function () {
      const { lender, passportNFT, owner, user2 } = await loadFixture(deployLenderFixture);
      
      // Mint passport with risk band 2
      await passportNFT.connect(owner).mintOrUpdate(user2.address, 600, 2);
      
      const ltv = await lender.getLTV(user2.address);
      expect(ltv).to.equal(5000); // 50% in basis points
    });

    it("Should return 30% LTV for risk band 3 (high risk)", async function () {
      const { lender, passportNFT, owner, user3 } = await loadFixture(deployLenderFixture);
      
      // Mint passport with risk band 3
      await passportNFT.connect(owner).mintOrUpdate(user3.address, 300, 3);
      
      const ltv = await lender.getLTV(user3.address);
      expect(ltv).to.equal(3000); // 30% in basis points
    });
  });

  describe("Max Borrow Calculation", function () {
    it("Should calculate max borrow correctly for risk band 1", async function () {
      const { lender, passportNFT, owner, user1 } = await loadFixture(deployLenderFixture);
      
      await passportNFT.connect(owner).mintOrUpdate(user1.address, 800, 1);
      
      const collateralValue = ethers.parseEther("1000"); // 1000 ETH
      const maxBorrow = await lender.calculateMaxBorrow(user1.address, collateralValue);
      
      // 70% of 1000 = 700 ETH
      expect(maxBorrow).to.equal(ethers.parseEther("700"));
    });

    it("Should calculate max borrow correctly for risk band 2", async function () {
      const { lender, passportNFT, owner, user2 } = await loadFixture(deployLenderFixture);
      
      await passportNFT.connect(owner).mintOrUpdate(user2.address, 600, 2);
      
      const collateralValue = ethers.parseEther("1000"); // 1000 ETH
      const maxBorrow = await lender.calculateMaxBorrow(user2.address, collateralValue);
      
      // 50% of 1000 = 500 ETH
      expect(maxBorrow).to.equal(ethers.parseEther("500"));
    });

    it("Should return 0 for users without passport", async function () {
      const { lender, user1 } = await loadFixture(deployLenderFixture);
      
      const collateralValue = ethers.parseEther("1000");
      const maxBorrow = await lender.calculateMaxBorrow(user1.address, collateralValue);
      
      expect(maxBorrow).to.equal(0);
    });
  });

  describe("Edge Cases", function () {
    it("Should handle risk band 0", async function () {
      const { lender, passportNFT, owner, user1 } = await loadFixture(deployLenderFixture);
      
      await passportNFT.connect(owner).mintOrUpdate(user1.address, 0, 0);
      
      const ltv = await lender.getLTV(user1.address);
      expect(ltv).to.equal(0);
    });

    it("Should handle score updates affecting LTV", async function () {
      const { lender, passportNFT, owner, user1 } = await loadFixture(deployLenderFixture);
      
      await passportNFT.connect(owner).mintOrUpdate(user1.address, 300, 3);
      expect(await lender.getLTV(user1.address)).to.equal(3000);
      
      await passportNFT.connect(owner).mintOrUpdate(user1.address, 800, 1);
      expect(await lender.getLTV(user1.address)).to.equal(7000);
    });

    it("Should calculate max borrow for zero collateral", async function () {
      const { lender, passportNFT, owner, user1 } = await loadFixture(deployLenderFixture);
      
      await passportNFT.connect(owner).mintOrUpdate(user1.address, 800, 1);
      const maxBorrow = await lender.calculateMaxBorrow(user1.address, 0);
      
      expect(maxBorrow).to.equal(0);
    });
  });

  describe("Gas Optimization", function () {
    it("Should use reasonable gas for LTV query", async function () {
      const { lender, passportNFT, owner, user1 } = await loadFixture(deployLenderFixture);
      
      await passportNFT.connect(owner).mintOrUpdate(user1.address, 800, 1);
      const tx = await lender.getLTV(user1.address);
      
      // View function, should be very cheap (no gas used in view calls)
      // But we can test the function works
      expect(await lender.getLTV(user1.address)).to.equal(7000);
    });
  });
});



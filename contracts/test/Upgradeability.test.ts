import { expect } from "chai";
import { ethers, upgrades } from "hardhat";
import { CreditPassportNFTV2 } from "../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("Contract Upgradeability", function () {
  let creditPassport: CreditPassportNFTV2;
  let admin: HardhatEthersSigner;
  let scoreUpdater: HardhatEthersSigner;
  let user: HardhatEthersSigner;
  let upgrader: HardhatEthersSigner;

  beforeEach(async function () {
    [admin, scoreUpdater, user, upgrader] = await ethers.getSigners();

    const CreditPassportNFTV2Factory = await ethers.getContractFactory("CreditPassportNFTV2");
    creditPassport = await upgrades.deployProxy(
      CreditPassportNFTV2Factory,
      [admin.address],
      { initializer: "initialize", kind: "uups" }
    ) as unknown as CreditPassportNFTV2;

    const SCORE_UPDATER_ROLE = await creditPassport.SCORE_UPDATER_ROLE();
    await creditPassport.grantRole(SCORE_UPDATER_ROLE, scoreUpdater.address);

    // Create some state
    await creditPassport.connect(scoreUpdater).mintOrUpdate(user.address, 750, 2);
  });

  it("Should preserve state after upgrade", async function () {
    // Get state before upgrade
    const scoreBefore = await creditPassport.getScore(user.address);
    const tokenIdBefore = await creditPassport.passportIdOf(user.address);

    // Grant UPGRADER_ROLE to admin (who will perform upgrade)
    const UPGRADER_ROLE = await creditPassport.UPGRADER_ROLE();
    await creditPassport.grantRole(UPGRADER_ROLE, admin.address);

    const CreditPassportNFTV2Factory = await ethers.getContractFactory("CreditPassportNFTV2");
    const upgraded = await upgrades.upgradeProxy(
      await creditPassport.getAddress(),
      CreditPassportNFTV2Factory
    ) as unknown as CreditPassportNFTV2;

    // Verify state preserved
    const scoreAfter = await upgraded.getScore(user.address);
    const tokenIdAfter = await upgraded.passportIdOf(user.address);

    expect(scoreAfter.score).to.equal(scoreBefore.score);
    expect(scoreAfter.riskBand).to.equal(scoreBefore.riskBand);
    expect(tokenIdAfter).to.equal(tokenIdBefore);
  });

  it("Should only allow upgrader role to upgrade", async function () {
    const CreditPassportNFTV2Factory = await ethers.getContractFactory("CreditPassportNFTV2");
    
    await expect(
      upgrades.upgradeProxy(
        await creditPassport.getAddress(),
        CreditPassportNFTV2Factory
      )
    ).to.be.reverted;
  });

  it("Should get implementation address", async function () {
    const implAddress = await upgrades.erc1967.getImplementationAddress(
      await creditPassport.getAddress()
    );
    expect(implAddress).to.not.equal(ethers.ZeroAddress);
  });

  it("Should get admin address", async function () {
    // For UUPS, there's no separate admin address - the admin role is in the implementation
    // Check that DEFAULT_ADMIN_ROLE is set correctly
    const DEFAULT_ADMIN_ROLE = await creditPassport.DEFAULT_ADMIN_ROLE();
    expect(await creditPassport.hasRole(DEFAULT_ADMIN_ROLE, admin.address)).to.be.true;
  });
});


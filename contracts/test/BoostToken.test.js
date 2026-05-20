const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BoostToken", function () {
  let owner, player, treasury;
  let usdc, boost;

  beforeEach(async function () {
    [owner, player, treasury] = await ethers.getSigners();
    const MockUSDC = await ethers.getContractFactory("MockUSDC");
    usdc = await MockUSDC.deploy("Mock USDC", "USDC");
    await usdc.waitForDeployment();

    const BoostToken = await ethers.getContractFactory("BoostToken");
    boost = await BoostToken.deploy(
      owner.address,
      await usdc.getAddress(),
      treasury.address,
      "https://coven-traders.io/api/boost/{id}.json"
    );
    await boost.waitForDeployment();

    await boost.createBoostType("Speed 2h", 7200, ethers.parseUnits("5", 6));
    await usdc.mint(player.address, ethers.parseUnits("100", 6));
    await usdc.connect(player).approve(await boost.getAddress(), ethers.parseUnits("100", 6));
  });

  it("should create boost type", async function () {
    const bt = await boost.boostTypes(0);
    expect(bt.name).to.equal("Speed 2h");
    expect(bt.durationSeconds).to.equal(7200);
    expect(bt.priceUSDC).to.equal(ethers.parseUnits("5", 6));
  });

  it("should purchase boost with USDC", async function () {
    await expect(boost.connect(player).purchase(0, 2))
      .to.emit(boost, "BoostPurchased")
      .withArgs(player.address, 0, 2, ethers.parseUnits("10", 6));
    expect(await boost.balanceOf(player.address, 0)).to.equal(2);
    expect(await usdc.balanceOf(treasury.address)).to.equal(ethers.parseUnits("10", 6));
  });

  it("should mint and burn", async function () {
    await boost.mint(player.address, 0, 5);
    expect(await boost.balanceOf(player.address, 0)).to.equal(5);
    await boost.connect(player).burn(player.address, 0, 2);
    expect(await boost.balanceOf(player.address, 0)).to.equal(3);
  });
});

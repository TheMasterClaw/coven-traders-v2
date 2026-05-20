const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Treasury", function () {
  let owner, operator, distributor, recipient;
  let usdc, treasury;

  beforeEach(async function () {
    [owner, operator, distributor, recipient] = await ethers.getSigners();

    const MockUSDC = await ethers.getContractFactory("MockUSDC");
    usdc = await MockUSDC.deploy("Mock USDC", "USDC");
    await usdc.waitForDeployment();

    const Treasury = await ethers.getContractFactory("Treasury");
    treasury = await Treasury.deploy(owner.address, 500);
    await treasury.waitForDeployment();

    await treasury.grantRole(await treasury.OPERATOR_ROLE(), operator.address);
    await treasury.grantRole(await treasury.DISTRIBUTOR_ROLE(), distributor.address);

    await usdc.mint(await treasury.getAddress(), ethers.parseUnits("1000", 6));
  });

  it("should record fee", async function () {
    await expect(treasury.connect(operator).recordFee(await usdc.getAddress(), ethers.parseUnits("100", 6), owner.address))
      .to.emit(treasury, "FeeCollected")
      .withArgs(await usdc.getAddress(), ethers.parseUnits("100", 6), owner.address);
    expect(await treasury.totalCollected(await usdc.getAddress())).to.equal(ethers.parseUnits("100", 6));
  });

  it("should distribute tokens", async function () {
    await treasury.connect(distributor).distribute(
      await usdc.getAddress(),
      ethers.parseUnits("200", 6),
      recipient.address,
      "rewards"
    );
    expect(await usdc.balanceOf(recipient.address)).to.equal(ethers.parseUnits("200", 6));
    expect(await treasury.totalDistributed(await usdc.getAddress())).to.equal(ethers.parseUnits("200", 6));
  });

  it("should update protocol fee", async function () {
    await treasury.setProtocolFee(1000);
    expect(await treasury.protocolFeeBps()).to.equal(1000);
  });

  it("should sweep token", async function () {
    await treasury.sweepToken(await usdc.getAddress(), recipient.address);
    expect(await usdc.balanceOf(recipient.address)).to.equal(ethers.parseUnits("1000", 6));
  });
});

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CrusadeEscrow", function () {
  let owner, operator, resolver, player1, player2, treasury;
  let usdc, escrow;

  beforeEach(async function () {
    [owner, operator, resolver, player1, player2, treasury] = await ethers.getSigners();

    const MockUSDC = await ethers.getContractFactory("MockUSDC");
    usdc = await MockUSDC.deploy("Mock USDC", "USDC");
    await usdc.waitForDeployment();

    const CrusadeEscrow = await ethers.getContractFactory("CrusadeEscrow");
    escrow = await CrusadeEscrow.deploy(owner.address, treasury.address, 500); // 5%
    await escrow.waitForDeployment();

    await escrow.grantRole(await escrow.OPERATOR_ROLE(), operator.address);
    await escrow.grantRole(await escrow.RESOLVER_ROLE(), resolver.address);

    // Mint USDC to players
    await usdc.mint(player1.address, ethers.parseUnits("1000", 6));
    await usdc.mint(player2.address, ethers.parseUnits("1000", 6));
    await usdc.connect(player1).approve(await escrow.getAddress(), ethers.parseUnits("1000", 6));
    await usdc.connect(player2).approve(await escrow.getAddress(), ethers.parseUnits("1000", 6));
  });

  it("should create a crusade", async function () {
    const now = Math.floor(Date.now() / 1000);
    const tx = await escrow.connect(operator).createCrusade(
      ethers.parseUnits("10", 6),
      now,
      now + 3600,
      await usdc.getAddress()
    );
    await expect(tx).to.emit(escrow, "CrusadeCreated").withArgs(0, ethers.parseUnits("10", 6), now, now + 3600);
    const c = await escrow.crusades(0);
    expect(c.entryFee).to.equal(ethers.parseUnits("10", 6));
  });

  it("should allow entry and split fee", async function () {
    const now = Math.floor(Date.now() / 1000);
    await escrow.connect(operator).createCrusade(
      ethers.parseUnits("100", 6),
      now,
      now + 3600,
      await usdc.getAddress()
    );

    await expect(escrow.connect(player1).enter(0))
      .to.emit(escrow, "Entered")
      .withArgs(0, player1.address, ethers.parseUnits("100", 6));

    const c = await escrow.crusades(0);
    expect(c.prizePool).to.equal(ethers.parseUnits("95", 6)); // 100 - 5%
    expect(c.protocolFee).to.equal(ethers.parseUnits("5", 6));
    expect(await usdc.balanceOf(treasury.address)).to.equal(ethers.parseUnits("5", 6));
  });

  it("should resolve and distribute prizes", async function () {
    const now = Math.floor(Date.now() / 1000);
    await escrow.connect(operator).createCrusade(
      ethers.parseUnits("100", 6),
      now,
      now + 1,
      await usdc.getAddress()
    );
    await escrow.connect(player1).enter(0);
    await escrow.connect(player2).enter(0);

    await ethers.provider.send("evm_increaseTime", [2]);
    await ethers.provider.send("evm_mine");

    const prize1 = ethers.parseUnits("90", 6);
    const prize2 = ethers.parseUnits("5", 6);
    await expect(escrow.connect(resolver).resolveCrusade(0, [player1.address, player2.address], [prize1, prize2]))
      .to.emit(escrow, "Resolved")
      .and.to.emit(escrow, "PrizeClaimed");

    expect(await usdc.balanceOf(player1.address)).to.equal(ethers.parseUnits("990", 6)); // 1000 - 100 + 90
    expect(await usdc.balanceOf(player2.address)).to.equal(ethers.parseUnits("905", 6)); // 1000 - 100 + 5
  });

  it("should not allow double entry", async function () {
    const now = Math.floor(Date.now() / 1000);
    await escrow.connect(operator).createCrusade(ethers.parseUnits("10", 6), now, now + 3600, await usdc.getAddress());
    await escrow.connect(player1).enter(0);
    await expect(escrow.connect(player1).enter(0)).to.be.revertedWith("CrusadeEscrow: already entered");
  });
});

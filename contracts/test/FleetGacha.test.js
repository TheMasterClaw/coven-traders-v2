const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FleetGacha", function () {
  let owner, player, treasury;
  let usdc, nft, gacha, vrfMock;

  beforeEach(async function () {
    [owner, player, treasury] = await ethers.getSigners();

    const MockUSDC = await ethers.getContractFactory("MockUSDC");
    usdc = await MockUSDC.deploy("Mock USDC", "USDC");
    await usdc.waitForDeployment();

    const DiscipleNFT = await ethers.getContractFactory("DiscipleNFT");
    nft = await DiscipleNFT.deploy(owner.address, await usdc.getAddress(), 0);
    await nft.waitForDeployment();

    const VRFCoordinatorV2Mock = await ethers.getContractFactory("VRFCoordinatorV2Mock");
    vrfMock = await VRFCoordinatorV2Mock.deploy();
    await vrfMock.waitForDeployment();

    const FleetGacha = await ethers.getContractFactory("FleetGacha");
    gacha = await FleetGacha.deploy(
      owner.address,
      await usdc.getAddress(),
      treasury.address,
      await nft.getAddress(),
      await vrfMock.getAddress(),
      "0x79d3d8832d904592c0bf9818b621522c988bb8b0c05cdc3b15aea1b6e8db0c15",
      1,
      500000,
      3
    );
    await gacha.waitForDeployment();

    await nft.grantRole(await nft.MINTER_ROLE(), await gacha.getAddress());

    // Rarity config: common(1)=5000, rare(2)=3000, epic(3)=1500, legendary(4)=400, mythic(5)=100
    await gacha.setRarityConfig(
      [1, 2, 3, 4, 5],
      [5000, 3000, 1500, 400, 100],
      [10, 50, 100, 200, 500],
      [49, 99, 199, 499, 999],
      ["uri1", "uri2", "uri3", "uri4", "uri5"]
    );

    await gacha.setRollPrice(ethers.parseUnits("10", 6));

    await usdc.mint(player.address, ethers.parseUnits("100", 6));
    await usdc.connect(player).approve(await gacha.getAddress(), ethers.parseUnits("100", 6));
  });

  it("should request roll on roll()", async function () {
    const tx = await gacha.connect(player).roll();
    await expect(tx).to.emit(gacha, "RollRequested");
    const req = await gacha.pendingRolls(0);
    expect(req.roller).to.equal(player.address);
  });

  it("should fulfill random words and mint NFT", async function () {
    await gacha.connect(player).roll();
    const randomWords = [ethers.toBigInt(ethers.randomBytes(32))];
    await expect(vrfMock.fulfillRandomWords(0, await gacha.getAddress(), randomWords))
      .to.emit(gacha, "RollFulfilled");
    expect(await nft.balanceOf(player.address)).to.equal(1);
  });

  it("should transfer USDC to treasury on roll", async function () {
    await gacha.connect(player).roll();
    expect(await usdc.balanceOf(treasury.address)).to.equal(ethers.parseUnits("10", 6));
  });
});

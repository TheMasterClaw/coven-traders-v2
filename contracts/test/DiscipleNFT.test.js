const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DiscipleNFT", function () {
  let owner, minter, player;
  let nft;

  beforeEach(async function () {
    [owner, minter, player] = await ethers.getSigners();
    const DiscipleNFT = await ethers.getContractFactory("DiscipleNFT");
    nft = await DiscipleNFT.deploy(owner.address, ethers.ZeroAddress, 0);
    await nft.waitForDeployment();
    await nft.grantRole(await nft.MINTER_ROLE(), minter.address);
  });

  it("should mint a disciple", async function () {
    const tx = await nft.connect(minter).mint(player.address, 1, 100, 3, "Alpha", "https://uri/1");
    await expect(tx).to.emit(nft, "DiscipleMinted").withArgs(player.address, 1, 1, 3);
    expect(await nft.ownerOf(1)).to.equal(player.address);
    const d = await nft.disciples(1);
    expect(d.fleetId).to.equal(1);
    expect(d.power).to.equal(100);
    expect(d.rarity).to.equal(3);
  });

  it("should batch mint", async function () {
    await nft.connect(minter).batchMint(
      [player.address, player.address],
      [1, 2],
      [100, 200],
      [2, 4],
      ["A", "B"],
      ["uri1", "uri2"]
    );
    expect(await nft.balanceOf(player.address)).to.equal(2);
  });

  it("should add XP", async function () {
    await nft.connect(minter).mint(player.address, 1, 100, 2, "X", "uri");
    await nft.connect(owner).addXp(1, 50);
    const d = await nft.disciples(1);
    expect(d.xp).to.equal(50);
  });

  it("should update token URI", async function () {
    await nft.connect(minter).mint(player.address, 1, 100, 2, "X", "uri");
    await nft.connect(owner).setTokenURI(1, "new-uri");
    expect(await nft.tokenURI(1)).to.equal("new-uri");
  });
});

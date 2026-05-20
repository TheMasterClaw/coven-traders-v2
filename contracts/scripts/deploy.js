const { ethers, upgrades } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  // Mock USDC for local/testnet (replace with real USDC on mainnet)
  const MockUSDC = await ethers.getContractFactory("MockUSDC");
  const usdc = await MockUSDC.deploy("Mock USDC", "USDC");
  await usdc.waitForDeployment();
  const usdcAddress = await usdc.getAddress();
  console.log("MockUSDC deployed to:", usdcAddress);

  // Treasury
  const Treasury = await ethers.getContractFactory("Treasury");
  const treasury = await Treasury.deploy(deployer.address, 500); // 5% protocol fee
  await treasury.waitForDeployment();
  const treasuryAddress = await treasury.getAddress();
  console.log("Treasury deployed to:", treasuryAddress);

  // DiscipleNFT
  const DiscipleNFT = await ethers.getContractFactory("DiscipleNFT");
  const discipleNFT = await DiscipleNFT.deploy(deployer.address, usdcAddress, 0);
  await discipleNFT.waitForDeployment();
  const discipleNFTAddress = await discipleNFT.getAddress();
  console.log("DiscipleNFT deployed to:", discipleNFTAddress);

  // BoostToken
  const BoostToken = await ethers.getContractFactory("BoostToken");
  const boostToken = await BoostToken.deploy(
    deployer.address,
    usdcAddress,
    treasuryAddress,
    "https://coven-traders.io/api/boost/{id}.json"
  );
  await boostToken.waitForDeployment();
  const boostTokenAddress = await boostToken.getAddress();
  console.log("BoostToken deployed to:", boostTokenAddress);

  // VRF Mock for local / testnet
  const VRFCoordinatorV2Mock = await ethers.getContractFactory("VRFCoordinatorV2Mock");
  const vrfMock = await VRFCoordinatorV2Mock.deploy();
  await vrfMock.waitForDeployment();
  const vrfAddress = await vrfMock.getAddress();
  console.log("VRFCoordinatorV2Mock deployed to:", vrfAddress);

  // FleetGacha
  const FleetGacha = await ethers.getContractFactory("FleetGacha");
  const fleetGacha = await FleetGacha.deploy(
    deployer.address,
    usdcAddress,
    treasuryAddress,
    discipleNFTAddress,
    vrfAddress,
    "0x79d3d8832d904592c0bf9818b621522c988bb8b0c05cdc3b15aea1b6e8db0c15", // dummy keyHash
    1, // subscriptionId
    500000, // callbackGasLimit
    3 // requestConfirmations
  );
  await fleetGacha.waitForDeployment();
  const fleetGachaAddress = await fleetGacha.getAddress();
  console.log("FleetGacha deployed to:", fleetGachaAddress);

  // CrusadeEscrow
  const CrusadeEscrow = await ethers.getContractFactory("CrusadeEscrow");
  const crusadeEscrow = await CrusadeEscrow.deploy(deployer.address, treasuryAddress, 500);
  await crusadeEscrow.waitForDeployment();
  const crusadeEscrowAddress = await crusadeEscrow.getAddress();
  console.log("CrusadeEscrow deployed to:", crusadeEscrowAddress);

  // Post-deployment configuration
  await (await discipleNFT.grantRole(await discipleNFT.MINTER_ROLE(), fleetGachaAddress)).wait();
  await (await discipleNFT.grantRole(await discipleNFT.MINTER_ROLE(), deployer.address)).wait();

  console.log("\nDeployment complete. Addresses:");
  console.log({
    usdc: usdcAddress,
    treasury: treasuryAddress,
    discipleNFT: discipleNFTAddress,
    boostToken: boostTokenAddress,
    vrfMock: vrfAddress,
    fleetGacha: fleetGachaAddress,
    crusadeEscrow: crusadeEscrowAddress,
  });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
import "./DiscipleNFT.sol";

/**
 * @title FleetGacha
 * @dev Random fleet drop gacha using Chainlink VRF v2.
 *      Players pay USDC to roll for DiscipleNFTs with weighted rarity.
 */
contract FleetGacha is AccessControl, ReentrancyGuard, VRFConsumerBaseV2 {
    using SafeERC20 for IERC20;

    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // Chainlink VRF
    VRFCoordinatorV2Interface public immutable vrfCoordinator;
    bytes32 public immutable keyHash;
    uint64 public immutable subscriptionId;
    uint32 public callbackGasLimit;
    uint16 public requestConfirmations;

    // Pricing
    address public paymentToken;
    uint256 public rollPrice; // USDC 6-decimal
    address public treasury;

    // Rarity weights (must sum to <= 10000 for convenience)
    struct RarityConfig {
        uint256 weight;    // out of 10000
        uint256 minPower;
        uint256 maxPower;
    }
    mapping(uint256 => RarityConfig) public rarityConfigs; // rarity id => config
    uint256[] public rarityIds;
    uint256 public totalWeight;

    // Pending rolls
    struct PendingRoll {
        address roller;
        uint256 paid;
    }
    mapping(uint256 => PendingRoll) public pendingRolls; // requestId => roll

    DiscipleNFT public discipleNFT;

    // URI templates per rarity
    mapping(uint256 => string) public rarityBaseURI;

    event RollRequested(uint256 indexed requestId, address indexed roller);
    event RollFulfilled(uint256 indexed requestId, uint256 indexed tokenId, uint256 rarity, uint256 power);
    event RollPriceUpdated(uint256 oldPrice, uint256 newPrice);
    event CallbackGasLimitUpdated(uint32 newLimit);

    constructor(
        address admin,
        address _paymentToken,
        address _treasury,
        address _discipleNFT,
        address _vrfCoordinator,
        bytes32 _keyHash,
        uint64 _subscriptionId,
        uint32 _callbackGasLimit,
        uint16 _requestConfirmations
    ) VRFConsumerBaseV2(_vrfCoordinator) {
        require(admin != address(0), "FleetGacha: zero admin");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);

        paymentToken = _paymentToken;
        treasury = _treasury;
        discipleNFT = DiscipleNFT(_discipleNFT);
        vrfCoordinator = VRFCoordinatorV2Interface(_vrfCoordinator);
        keyHash = _keyHash;
        subscriptionId = _subscriptionId;
        callbackGasLimit = _callbackGasLimit;
        requestConfirmations = _requestConfirmations;
    }

    function setRarityConfig(
        uint256[] calldata _rarityIds,
        uint256[] calldata weights,
        uint256[] calldata minPowers,
        uint256[] calldata maxPowers,
        string[] calldata baseURIs
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 n = _rarityIds.length;
        require(
            n == weights.length && n == minPowers.length && n == maxPowers.length && n == baseURIs.length,
            "FleetGacha: array length mismatch"
        );
        delete rarityIds;
        uint256 tw = 0;
        for (uint256 i = 0; i < n; i++) {
            uint256 rid = _rarityIds[i];
            rarityConfigs[rid] = RarityConfig({
                weight: weights[i],
                minPower: minPowers[i],
                maxPower: maxPowers[i]
            });
            rarityBaseURI[rid] = baseURIs[i];
            rarityIds.push(rid);
            tw += weights[i];
        }
        require(tw <= 10000, "FleetGacha: total weight > 10000");
        totalWeight = tw;
    }

    function setRollPrice(uint256 newPrice) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 old = rollPrice;
        rollPrice = newPrice;
        emit RollPriceUpdated(old, newPrice);
    }

    function setCallbackGasLimit(uint32 _limit) external onlyRole(DEFAULT_ADMIN_ROLE) {
        callbackGasLimit = _limit;
        emit CallbackGasLimitUpdated(_limit);
    }

    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        treasury = _treasury;
    }

    /**
     * @notice Initiate a gacha roll. Transfers USDC and requests VRF randomness.
     */
    function roll() external nonReentrant returns (uint256 requestId) {
        require(rollPrice > 0, "FleetGacha: price not set");
        require(totalWeight > 0, "FleetGacha: rarities not set");
        require(address(discipleNFT) != address(0), "FleetGacha: nft not set");

        // Pull payment
        IERC20(paymentToken).safeTransferFrom(msg.sender, treasury, rollPrice);

        requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            1 // numWords = 1
        );

        pendingRolls[requestId] = PendingRoll({
            roller: msg.sender,
            paid: rollPrice
        });

        emit RollRequested(requestId, msg.sender);
    }

    /**
     * @dev Chainlink VRF callback.
     */
    function fulfillRandomWords(uint256 requestId, uint256[] memory randomWords) internal override {
        PendingRoll memory roll = pendingRolls[requestId];
        require(roll.roller != address(0), "FleetGacha: unknown request");

        uint256 rand = randomWords[0];
        uint256 rarity = _pickRarity(rand);
        RarityConfig memory rc = rarityConfigs[rarity];

        // Derive power within range using remaining entropy
        uint256 powerRange = rc.maxPower - rc.minPower + 1;
        uint256 power = rc.minPower + (rand % powerRange);

        // Mint DiscipleNFT
        uint256 tokenId = discipleNFT.mint(
            roll.roller,
            rand % 10000, // fleetId derived from entropy
            power,
            rarity,
            _generateName(rarity, tokenId),
            rarityBaseURI[rarity]
        );

        delete pendingRolls[requestId];
        emit RollFulfilled(requestId, tokenId, rarity, power);
    }

    function _pickRarity(uint256 rand) internal view returns (uint256) {
        uint256 rollPoint = rand % totalWeight;
        uint256 cumulative = 0;
        for (uint256 i = 0; i < rarityIds.length; i++) {
            uint256 rid = rarityIds[i];
            cumulative += rarityConfigs[rid].weight;
            if (rollPoint < cumulative) {
                return rid;
            }
        }
        // fallback to last rarity
        return rarityIds[rarityIds.length - 1];
    }

    function _generateName(uint256 rarity, uint256 tokenId) internal pure returns (string memory) {
        // Minimal on-chain name generation; frontend can override metadata
        return string(abi.encodePacked("Disciple #", _uint2str(tokenId), "-R", _uint2str(rarity)));
    }

    function _uint2str(uint256 _i) internal pure returns (string memory) {
        if (_i == 0) return "0";
        uint256 j = _i;
        uint256 len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint256 k = len;
        while (_i != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(_i - (_i / 10) * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        return string(bstr);
    }
}

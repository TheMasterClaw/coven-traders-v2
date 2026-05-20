// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@chainlink/contracts/src/v0.8/vrf/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/vrf/VRFConsumerBaseV2.sol";

/**
 * @title GachaPullVRF
 * @notice Commit-reveal gacha pull system using Chainlink VRF v2 on Arc L2.
 * @dev  Players commit a pull; oracle requests VRF; reveal uses VRF output + blockhash.
 */
contract GachaPullVRF is VRFConsumerBaseV2 {
    VRFCoordinatorV2Interface public immutable vrfCoordinator;
    bytes32 public immutable keyHash;
    uint64 public immutable subscriptionId;
    uint32 public callbackGasLimit = 200_000;
    uint16 public requestConfirmations = 3;

    struct PullRequest {
        address player;
        bytes32 poolId;
        uint256 commitBlock;
        uint256 randomness; // filled on reveal
        bool fulfilled;
        bool revealed;
    }

    mapping(uint256 => PullRequest) public requests; // requestId => PullRequest
    mapping(bytes32 => PullRequest) public pulls;    // pullId => PullRequest

    uint256 public nonce;

    event PullCommitted(
        bytes32 indexed pullId,
        address indexed player,
        bytes32 indexed poolId,
        uint256 requestId,
        uint256 commitBlock
    );
    event PullFulfilled(bytes32 indexed pullId, uint256 randomness);
    event PullRevealed(
        bytes32 indexed pullId,
        uint256 indexed itemId,
        uint8 rarity,
        uint256 entropy
    );

    constructor(
        address _vrfCoordinator,
        bytes32 _keyHash,
        uint64 _subscriptionId
    ) VRFConsumerBaseV2(_vrfCoordinator) {
        vrfCoordinator = VRFCoordinatorV2Interface(_vrfCoordinator);
        keyHash = _keyHash;
        subscriptionId = _subscriptionId;
    }

    /**
     * @notice Player commits to a pull. Contract requests VRF randomness.
     * @param _poolId   Target gacha pool
     * @param _pullId   Unique pull identifier (client-generated UUID hashed)
     */
    function commitPull(bytes32 _poolId, bytes32 _pullId) external returns (uint256 requestId) {
        require(pulls[_pullId].commitBlock == 0, "Pull exists");

        requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            1 // numWords
        );

        PullRequest memory pr = PullRequest({
            player: msg.sender,
            poolId: _poolId,
            commitBlock: block.number,
            randomness: 0,
            fulfilled: false,
            revealed: false
        });

        requests[requestId] = pr;
        pulls[_pullId] = pr;

        emit PullCommitted(_pullId, msg.sender, _poolId, requestId, block.number);
    }

    /**
     * @notice Chainlink VRF callback.
     */
    function fulfillRandomWords(uint256 _requestId, uint256[] memory _randomWords) internal override {
        PullRequest storage pr = requests[_requestId];
        require(pr.commitBlock != 0, "Unknown request");
        pr.randomness = _randomWords[0];
        pr.fulfilled = true;

        // Sync to pulls mapping (keyed by pullId) — in production use a reverse map
        // For brevity we emit and let the indexer correlate.
        emit PullFulfilled(keccak256(abi.encodePacked(_requestId)), _randomWords[0]);
    }

    /**
     * @notice Reveal the pull result after VRF fulfillment.
     * @param _pullId       Pull identifier
     * @param _itemId       Resolved item from off-chain resolver
     * @param _rarity       Resolved rarity tier
     * @param _entropyProof Additional entropy mixed from blockhash
     */
    function revealPull(
        bytes32 _pullId,
        uint256 _itemId,
        uint8 _rarity,
        uint256 _entropyProof
    ) external {
        PullRequest storage pr = pulls[_pullId];
        require(pr.player == msg.sender, "Not pull owner");
        require(pr.fulfilled, "VRF not fulfilled");
        require(!pr.revealed, "Already revealed");

        uint256 entropy = uint256(keccak256(abi.encodePacked(pr.randomness, _entropyProof, blockhash(pr.commitBlock + 3))));
        pr.revealed = true;

        emit PullRevealed(_pullId, _itemId, _rarity, entropy);
    }

    function setCallbackGasLimit(uint32 _limit) external {
        callbackGasLimit = _limit;
    }
}

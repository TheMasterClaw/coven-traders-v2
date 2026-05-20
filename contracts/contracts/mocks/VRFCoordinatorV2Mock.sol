// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";

/**
 * @title VRFCoordinatorV2Mock
 * @dev Minimal mock for Chainlink VRF v2 for local testing.
 */
contract VRFCoordinatorV2Mock is VRFCoordinatorV2Interface {
    uint256 public requestCount;
    mapping(uint256 => address) public consumers;
    mapping(uint256 => uint256) public requestBlock;

    event RandomWordsRequested(
        bytes32 keyHash,
        uint256 requestId,
        uint256 preSeed,
        uint64 subId,
        uint16 minimumRequestConfirmations,
        uint32 callbackGasLimit,
        uint32 numWords,
        address indexed sender
    );

    function requestRandomWords(
        bytes32 keyHash,
        uint64 subId,
        uint16 minimumRequestConfirmations,
        uint32 callbackGasLimit,
        uint32 numWords
    ) external override returns (uint256 requestId) {
        requestId = requestCount;
        consumers[requestId] = msg.sender;
        requestBlock[requestId] = block.number;
        requestCount++;
        emit RandomWordsRequested(
            keyHash,
            requestId,
            uint256(keccak256(abi.encodePacked(blockhash(block.number - 1), msg.sender, requestId))),
            subId,
            minimumRequestConfirmations,
            callbackGasLimit,
            numWords,
            msg.sender
        );
    }

    function fulfillRandomWords(uint256 requestId, address consumer, uint256[] memory randomWords) external {
        (bool success, ) = consumer.call(
            abi.encodeWithSignature("rawFulfillRandomWords(uint256,uint256[])", requestId, randomWords)
        );
        require(success, "VRFCoordinatorV2Mock: fulfill failed");
    }

    function getRequestConfig() external pure override returns (uint16, uint32, bytes32[] memory) {
        return (3, 2000000, new bytes32[](0));
    }

    function addConsumer(uint64 subId, address consumer) external override {}
    function cancelSubscription(uint64 subId, address to) external override {}
    function acceptSubscriptionOwnerTransfer(uint64 subId) external override {}
    function requestSubscriptionOwnerTransfer(uint64 subId, address newOwner) external override {}
    function removeConsumer(uint64 subId, address consumer) external override {}
    function getSubscription(uint64 subId) external pure override returns (uint96, uint64, address, address[] memory) {
        return (0, 0, address(0), new address[](0));
    }
    function createSubscription() external pure override returns (uint64 subId) {
        return 1;
    }
    function fundSubscription(uint64 subId, uint96 amount) external override {}
}

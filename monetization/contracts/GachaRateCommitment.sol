// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title GachaRateCommitment
 * @notice On-chain verifiable drop-rate commitment for Agora Coven Traders gacha pools.
 * @dev  Daily rate hashes are committed by an authorized oracle. Players can verify
 *       that pull results match the committed rates via entropy proofs.
 */
contract GachaRateCommitment {
    address public owner;
    address public oracle;

    struct Commitment {
        bytes32 commitmentHash;
        uint256 timestamp;
        bool revealed;
    }

    // poolId => day (UTC midnight) => Commitment
    mapping(bytes32 => mapping(uint256 => Commitment)) public commitments;
    mapping(bytes32 => bool) public authorizedPools;

    event PoolAuthorized(bytes32 indexed poolId, string name);
    event RateCommitted(
        bytes32 indexed poolId,
        bytes32 indexed commitmentHash,
        uint256 day
    );
    event OracleUpdated(address indexed oldOracle, address indexed newOracle);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyOracle() {
        require(msg.sender == oracle, "Not oracle");
        _;
    }

    constructor(address _oracle) {
        owner = msg.sender;
        oracle = _oracle;
    }

    function setOracle(address _newOracle) external onlyOwner {
        emit OracleUpdated(oracle, _newOracle);
        oracle = _newOracle;
    }

    function authorizePool(bytes32 _poolId, string calldata _name) external onlyOwner {
        authorizedPools[_poolId] = true;
        emit PoolAuthorized(_poolId, _name);
    }

    /**
     * @notice Commit the keccak256 hash of the day's drop-rate JSON.
     * @param _poolId   Pool identifier (e.g., keccak256("standard"))
     * @param _day      UTC midnight timestamp for the day
     * @param _hash     keccak256(JSON_without_verification_field)
     */
    function commitRate(
        bytes32 _poolId,
        uint256 _day,
        bytes32 _hash
    ) external onlyOracle {
        require(authorizedPools[_poolId], "Pool not authorized");
        require(commitments[_poolId][_day].timestamp == 0, "Already committed");

        commitments[_poolId][_day] = Commitment({
            commitmentHash: _hash,
            timestamp: block.timestamp,
            revealed: false
        });

        emit RateCommitted(_poolId, _hash, _day);
    }

    /**
     * @notice Verify that a given rate JSON matches a prior commitment.
     * @param _poolId   Pool identifier
     * @param _day      UTC midnight timestamp
     * @param _jsonHash Hash of the JSON being verified
     */
    function verifyCommitment(
        bytes32 _poolId,
        uint256 _day,
        bytes32 _jsonHash
    ) external view returns (bool) {
        Commitment memory c = commitments[_poolId][_day];
        require(c.timestamp != 0, "No commitment for day");
        return c.commitmentHash == _jsonHash;
    }

    /**
     * @notice Mark a commitment as revealed after VRF callback.
     */
    function markRevealed(bytes32 _poolId, uint256 _day) external onlyOracle {
        require(commitments[_poolId][_day].timestamp != 0, "No commitment");
        commitments[_poolId][_day].revealed = true;
    }
}

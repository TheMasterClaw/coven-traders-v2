// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title CrusadeEscrow
 * @dev Tournament entry escrow, prize distribution, and protocol fee routing for Coven Traders.
 *      Players deposit USDC to enter crusades. Prizes are distributed after tournament resolution.
 */
contract CrusadeEscrow is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant RESOLVER_ROLE = keccak256("RESOLVER_ROLE");

    struct Crusade {
        uint256 entryFee;
        uint256 prizePool;
        uint256 protocolFee;
        uint256 startTime;
        uint256 endTime;
        bool resolved;
        address paymentToken;
        address[] entrants;
        mapping(address => bool) hasEntered;
        mapping(address => uint256) placement; // 1 = first place
        mapping(uint256 => address) placementToEntrant;
    }

    mapping(uint256 => Crusade) public crusades;
    uint256 public crusadeCount;

    address public treasury;
    uint256 public protocolFeeBps; // basis points taken from each entry

    event CrusadeCreated(uint256 indexed crusadeId, uint256 entryFee, uint256 startTime, uint256 endTime);
    event Entered(uint256 indexed crusadeId, address indexed entrant, uint256 feePaid);
    event Resolved(uint256 indexed crusadeId, address[] winners, uint256[] prizes);
    event PrizeClaimed(uint256 indexed crusadeId, address indexed winner, uint256 amount);
    event ProtocolFeeUpdated(uint256 oldFee, uint256 newFee);
    event TreasuryUpdated(address indexed newTreasury);

    constructor(address admin, address _treasury, uint256 _protocolFeeBps) {
        require(admin != address(0), "CrusadeEscrow: zero admin");
        require(_treasury != address(0), "CrusadeEscrow: zero treasury");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
        _grantRole(RESOLVER_ROLE, admin);
        treasury = _treasury;
        protocolFeeBps = _protocolFeeBps;
    }

    function createCrusade(
        uint256 entryFee,
        uint256 startTime,
        uint256 endTime,
        address paymentToken
    ) external onlyRole(OPERATOR_ROLE) returns (uint256 crusadeId) {
        require(startTime < endTime, "CrusadeEscrow: invalid times");
        require(paymentToken != address(0), "CrusadeEscrow: zero token");
        crusadeId = crusadeCount;
        Crusade storage c = crusades[crusadeId];
        c.entryFee = entryFee;
        c.startTime = startTime;
        c.endTime = endTime;
        c.paymentToken = paymentToken;
        c.resolved = false;
        crusadeCount++;
        emit CrusadeCreated(crusadeId, entryFee, startTime, endTime);
    }

    function enter(uint256 crusadeId) external nonReentrant {
        Crusade storage c = crusades[crusadeId];
        require(block.timestamp >= c.startTime, "CrusadeEscrow: not started");
        require(block.timestamp <= c.endTime, "CrusadeEscrow: ended");
        require(!c.hasEntered[msg.sender], "CrusadeEscrow: already entered");
        require(c.entryFee > 0, "CrusadeEscrow: no entry fee");

        uint256 fee = c.entryFee;
        uint256 protocolFee = (fee * protocolFeeBps) / 10000;
        uint256 poolContribution = fee - protocolFee;

        IERC20(c.paymentToken).safeTransferFrom(msg.sender, treasury, protocolFee);
        IERC20(c.paymentToken).safeTransferFrom(msg.sender, address(this), poolContribution);

        c.prizePool += poolContribution;
        c.protocolFee += protocolFee;
        c.hasEntered[msg.sender] = true;
        c.entrants.push(msg.sender);

        emit Entered(crusadeId, msg.sender, fee);
    }

    function resolveCrusade(
        uint256 crusadeId,
        address[] calldata winners,
        uint256[] calldata prizes
    ) external onlyRole(RESOLVER_ROLE) nonReentrant {
        Crusade storage c = crusades[crusadeId];
        require(block.timestamp > c.endTime, "CrusadeEscrow: not ended");
        require(!c.resolved, "CrusadeEscrow: already resolved");
        require(winners.length == prizes.length, "CrusadeEscrow: length mismatch");

        uint256 totalPrize;
        for (uint256 i = 0; i < prizes.length; i++) {
            totalPrize += prizes[i];
        }
        require(totalPrize <= c.prizePool, "CrusadeEscrow: prizes exceed pool");

        for (uint256 i = 0; i < winners.length; i++) {
            require(c.hasEntered[winners[i]], "CrusadeEscrow: winner not entrant");
            c.placement[winners[i]] = i + 1;
            c.placementToEntrant[i + 1] = winners[i];
        }

        c.resolved = true;
        emit Resolved(crusadeId, winners, prizes);

        // Distribute prizes immediately (push) for simplicity; could be pull pattern.
        for (uint256 i = 0; i < winners.length; i++) {
            if (prizes[i] > 0) {
                IERC20(c.paymentToken).safeTransfer(winners[i], prizes[i]);
                emit PrizeClaimed(crusadeId, winners[i], prizes[i]);
            }
        }

        // Remainder stays in contract as surplus or can be swept by admin
    }

    function setProtocolFee(uint256 newFeeBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newFeeBps <= 3000, "CrusadeEscrow: fee too high");
        uint256 old = protocolFeeBps;
        protocolFeeBps = newFeeBps;
        emit ProtocolFeeUpdated(old, newFeeBps);
    }

    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_treasury != address(0), "CrusadeEscrow: zero treasury");
        treasury = _treasury;
        emit TreasuryUpdated(_treasury);
    }

    function sweepSurplus(uint256 crusadeId, address to) external onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant {
        Crusade storage c = crusades[crusadeId];
        require(c.resolved, "CrusadeEscrow: not resolved");
        uint256 bal = IERC20(c.paymentToken).balanceOf(address(this));
        require(bal > 0, "CrusadeEscrow: no surplus");
        IERC20(c.paymentToken).safeTransfer(to, bal);
    }

    function getEntrants(uint256 crusadeId) external view returns (address[] memory) {
        return crusades[crusadeId].entrants;
    }

    function hasEntered(uint256 crusadeId, address account) external view returns (bool) {
        return crusades[crusadeId].hasEntered[account];
    }
}

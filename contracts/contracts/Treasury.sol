// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title Treasury
 * @dev Protocol fee collection and distribution hub for Coven Traders.
 *      Holds USDC and other tokens collected from tournaments, gacha, and marketplace.
 */
contract Treasury is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant DISTRIBUTOR_ROLE = keccak256("DISTRIBUTOR_ROLE");

    // Protocol fee percentages (basis points: 100 = 1%)
    uint256 public protocolFeeBps; // default e.g. 500 = 5%
    uint256 public constant MAX_FEE_BPS = 3000; // 30% hard cap

    // Tracking
    mapping(address => uint256) public totalCollected;
    mapping(address => uint256) public totalDistributed;

    event FeeCollected(address indexed token, uint256 amount, address indexed source);
    event Distributed(address indexed token, uint256 amount, address indexed recipient, string reason);
    event ProtocolFeeUpdated(uint256 oldFee, uint256 newFee);
    event Swept(address indexed token, uint256 amount, address indexed to);

    constructor(address admin, uint256 _protocolFeeBps) {
        require(admin != address(0), "Treasury: zero admin");
        require(_protocolFeeBps <= MAX_FEE_BPS, "Treasury: fee too high");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
        _grantRole(DISTRIBUTOR_ROLE, admin);
        protocolFeeBps = _protocolFeeBps;
    }

    /**
     * @notice Record a fee collection (pull pattern). Tokens should be transferred to this contract first.
     */
    function recordFee(address token, uint256 amount, address source) external onlyRole(OPERATOR_ROLE) {
        require(token != address(0), "Treasury: zero token");
        require(amount > 0, "Treasury: zero amount");
        uint256 bal = IERC20(token).balanceOf(address(this));
        require(bal >= totalCollected[token] + amount, "Treasury: insufficient balance recorded");
        totalCollected[token] += amount;
        emit FeeCollected(token, amount, source);
    }

    /**
     * @notice Distribute tokens to a recipient (e.g., team, rewards pool).
     */
    function distribute(
        address token,
        uint256 amount,
        address recipient,
        string calldata reason
    ) external onlyRole(DISTRIBUTOR_ROLE) nonReentrant {
        require(token != address(0), "Treasury: zero token");
        require(recipient != address(0), "Treasury: zero recipient");
        require(amount > 0, "Treasury: zero amount");
        uint256 available = IERC20(token).balanceOf(address(this));
        require(available >= amount, "Treasury: insufficient balance");
        totalDistributed[token] += amount;
        IERC20(token).safeTransfer(recipient, amount);
        emit Distributed(token, amount, recipient, reason);
    }

    /**
     * @notice Update protocol fee rate.
     */
    function setProtocolFee(uint256 newFeeBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(newFeeBps <= MAX_FEE_BPS, "Treasury: fee too high");
        uint256 old = protocolFeeBps;
        protocolFeeBps = newFeeBps;
        emit ProtocolFeeUpdated(old, newFeeBps);
    }

    /**
     * @notice Sweep accidental ETH (if any). Arc is EVM-compatible; payable fallback not expected but safeguarded.
     */
    function sweepETH(address payable to) external onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant {
        require(to != address(0), "Treasury: zero to");
        uint256 bal = address(this).balance;
        require(bal > 0, "Treasury: no ETH");
        (bool ok, ) = to.call{value: bal}("");
        require(ok, "Treasury: ETH sweep failed");
    }

    /**
     * @notice Sweep ERC20 in case of stuck tokens.
     */
    function sweepToken(address token, address to) external onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant {
        require(token != address(0), "Treasury: zero token");
        require(to != address(0), "Treasury: zero to");
        uint256 bal = IERC20(token).balanceOf(address(this));
        require(bal > 0, "Treasury: no token");
        IERC20(token).safeTransfer(to, bal);
        emit Swept(token, bal, to);
    }

    receive() external payable {}
}

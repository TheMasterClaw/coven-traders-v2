// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title BoostToken
 * @dev ERC1155 time-accelerator consumables for Coven Traders.
 *      Each token ID represents a boost type (e.g., 1=2h speedup, 2=8h speedup).
 */
contract BoostToken is ERC1155, AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");

    struct BoostType {
        string name;
        uint256 durationSeconds; // how much time it accelerates
        uint256 priceUSDC;       // 6-decimal USDC price
        bool enabled;
    }

    mapping(uint256 => BoostType) public boostTypes;
    uint256 public boostTypeCount;

    address public paymentToken; // USDC
    address public treasury;

    event BoostTypeCreated(uint256 indexed id, string name, uint256 duration, uint256 price);
    event BoostPurchased(address indexed buyer, uint256 indexed boostId, uint256 amount, uint256 totalCost);
    event BoostBurned(address indexed burner, uint256 indexed boostId, uint256 amount);
    event TreasuryUpdated(address indexed newTreasury);

    constructor(
        address admin,
        address _paymentToken,
        address _treasury,
        string memory uri
    ) ERC1155(uri) {
        require(admin != address(0), "BoostToken: zero admin");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(BURNER_ROLE, admin);
        paymentToken = _paymentToken;
        treasury = _treasury;
    }

    function createBoostType(
        string calldata name,
        uint256 durationSeconds,
        uint256 priceUSDC
    ) external onlyRole(DEFAULT_ADMIN_ROLE) returns (uint256 id) {
        id = boostTypeCount;
        boostTypes[id] = BoostType({
            name: name,
            durationSeconds: durationSeconds,
            priceUSDC: priceUSDC,
            enabled: true
        });
        boostTypeCount++;
        emit BoostTypeCreated(id, name, durationSeconds, priceUSDC);
    }

    function setBoostEnabled(uint256 id, bool enabled) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(id < boostTypeCount, "BoostToken: invalid id");
        boostTypes[id].enabled = enabled;
    }

    function setBoostPrice(uint256 id, uint256 priceUSDC) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(id < boostTypeCount, "BoostToken: invalid id");
        boostTypes[id].priceUSDC = priceUSDC;
    }

    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_treasury != address(0), "BoostToken: zero treasury");
        treasury = _treasury;
        emit TreasuryUpdated(_treasury);
    }

    /**
     * @notice Purchase boost tokens with USDC.
     */
    function purchase(uint256 boostId, uint256 amount) external nonReentrant {
        require(boostId < boostTypeCount, "BoostToken: invalid boost id");
        BoostType memory bt = boostTypes[boostId];
        require(bt.enabled, "BoostToken: boost not enabled");
        require(amount > 0, "BoostToken: zero amount");
        uint256 totalCost = bt.priceUSDC * amount;
        require(totalCost > 0, "BoostToken: zero cost");

        IERC20(paymentToken).safeTransferFrom(msg.sender, treasury, totalCost);
        _mint(msg.sender, boostId, amount, "");
        emit BoostPurchased(msg.sender, boostId, amount, totalCost);
    }

    function mint(address to, uint256 id, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, id, amount, "");
    }

    function mintBatch(
        address to,
        uint256[] calldata ids,
        uint256[] calldata amounts
    ) external onlyRole(MINTER_ROLE) {
        _mintBatch(to, ids, amounts, "");
    }

    function burn(address from, uint256 id, uint256 amount) external {
        require(
            from == msg.sender || isApprovedForAll(from, msg.sender) || hasRole(BURNER_ROLE, msg.sender),
            "BoostToken: caller not owner nor approved nor burner"
        );
        _burn(from, id, amount);
        emit BoostBurned(from, id, amount);
    }

    function burnBatch(address from, uint256[] calldata ids, uint256[] calldata amounts) external {
        require(
            from == msg.sender || isApprovedForAll(from, msg.sender) || hasRole(BURNER_ROLE, msg.sender),
            "BoostToken: caller not owner nor approved nor burner"
        );
        _burnBatch(from, ids, amounts);
        for (uint256 i = 0; i < ids.length; i++) {
            emit BoostBurned(from, ids[i], amounts[i]);
        }
    }

    function uri(uint256) public view override returns (string memory) {
        return super.uri(0);
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC1155, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title ShopUSDC
 * @notice In-game shop accepting USDC on Arc L2.
 * @dev  Purchases emit events for the analytics indexer. Supports consumables,
 *       non-consumables, bundles, and seasonal sales.
 */
contract ShopUSDC is Ownable, ReentrancyGuard {
    IERC20 public usdc;
    address public treasury;
    address public feeRecipient;
    uint16 public platformFeeBps = 1000; // 10%

    struct SKU {
        bytes32 skuId;
        uint256 price;          // in USDC wei (6 decimals)
        uint16 maxQtyPerTxn;
        bool active;
        bool consumable;
        uint256 salePrice;      // 0 = no sale
        uint256 saleEnd;        // timestamp
    }

    mapping(bytes32 => SKU) public skus;
    mapping(address => mapping(bytes32 => uint256)) public ownedNonConsumables;
    mapping(bytes32 => bool) public bundleIds;

    event Purchase(
        address indexed buyer,
        bytes32 indexed skuId,
        uint256 quantity,
        uint256 totalPrice,
        bytes32 indexed bundleId,
        uint256 timestamp
    );
    event SKUAdded(bytes32 indexed skuId, uint256 price);
    event SKUUpdated(bytes32 indexed skuId, uint256 newPrice);
    event BundleRegistered(bytes32 indexed bundleId);
    event Withdrawal(address indexed to, uint256 amount);

    constructor(address _usdc, address _treasury, address _feeRecipient) Ownable(msg.sender) {
        usdc = IERC20(_usdc);
        treasury = _treasury;
        feeRecipient = _feeRecipient;
    }

    function addSKU(
        bytes32 _skuId,
        uint256 _price,
        uint16 _maxQtyPerTxn,
        bool _consumable
    ) external onlyOwner {
        skus[_skuId] = SKU({
            skuId: _skuId,
            price: _price,
            maxQtyPerTxn: _maxQtyPerTxn,
            active: true,
            consumable: _consumable,
            salePrice: 0,
            saleEnd: 0
        });
        emit SKUAdded(_skuId, _price);
    }

    function setSale(bytes32 _skuId, uint256 _salePrice, uint256 _saleEnd) external onlyOwner {
        require(skus[_skuId].skuId == _skuId, "SKU not found");
        skus[_skuId].salePrice = _salePrice;
        skus[_skuId].saleEnd = _saleEnd;
    }

    function registerBundle(bytes32 _bundleId) external onlyOwner {
        bundleIds[_bundleId] = true;
        emit BundleRegistered(_bundleId);
    }

    function purchase(bytes32 _skuId, uint256 _quantity, bytes32 _bundleId) external nonReentrant {
        SKU storage sku = skus[_skuId];
        require(sku.active, "SKU inactive");
        require(_quantity > 0 && _quantity <= sku.maxQtyPerTxn, "Invalid qty");
        if (!sku.consumable) {
            require(ownedNonConsumables[msg.sender][_skuId] == 0, "Already owned");
        }

        uint256 unitPrice = (sku.salePrice > 0 && block.timestamp <= sku.saleEnd) ? sku.salePrice : sku.price;
        uint256 total = unitPrice * _quantity;

        uint256 fee = (total * platformFeeBps) / 10000;
        uint256 net = total - fee;

        require(usdc.transferFrom(msg.sender, feeRecipient, fee), "Fee transfer failed");
        require(usdc.transferFrom(msg.sender, treasury, net), "Treasury transfer failed");

        if (!sku.consumable) {
            ownedNonConsumables[msg.sender][_skuId] += _quantity;
        }

        emit Purchase(msg.sender, _skuId, _quantity, total, _bundleId, block.timestamp);
    }

    function withdrawERC20(address _token, uint256 _amount) external onlyOwner {
        require(IERC20(_token).transfer(treasury, _amount), "Withdraw failed");
        emit Withdrawal(treasury, _amount);
    }

    function setPlatformFee(uint16 _bps) external onlyOwner {
        require(_bps <= 3000, "Max 30%");
        platformFeeBps = _bps;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title BoostToken
/// @notice ERC-1155 for consumable boosts (time accelerators, multipliers)
contract BoostToken is ERC1155, Ownable {
    
    struct BoostType {
        string name;
        uint256 multiplierBp; // basis points, e.g. 20000 = 2x
        uint256 durationSeconds;
        uint256 maxSupply;
        uint256 minted;
        bool exists;
    }
    
    mapping(uint256 => BoostType) public boostTypes;
    uint256 public nextBoostTypeId;
    
    // Track active boosts per player: player => boostTypeId => expiry timestamp
    mapping(address => mapping(uint256 => uint256)) public activeBoosts;
    
    event BoostTypeCreated(uint256 indexed id, string name, uint256 multiplierBp);
    event BoostActivated(address indexed player, uint256 indexed boostTypeId, uint256 expiry);
    
    constructor(string memory uri) ERC1155(uri) Ownable(msg.sender) {}
    
    function createBoostType(
        string memory name,
        uint256 multiplierBp,
        uint256 durationSeconds,
        uint256 maxSupply
    ) external onlyOwner returns (uint256) {
        uint256 id = nextBoostTypeId++;
        boostTypes[id] = BoostType({
            name: name,
            multiplierBp: multiplierBp,
            durationSeconds: durationSeconds,
            maxSupply: maxSupply,
            minted: 0,
            exists: true
        });
        emit BoostTypeCreated(id, name, multiplierBp);
        return id;
    }
    
    function mintBoost(address to, uint256 boostTypeId, uint256 amount) external onlyOwner {
        BoostType storage bt = boostTypes[boostTypeId];
        require(bt.exists, "Boost type does not exist");
        require(bt.minted + amount <= bt.maxSupply, "Max supply reached");
        bt.minted += amount;
        _mint(to, boostTypeId, amount, "");
    }
    
    function activateBoost(uint256 boostTypeId) external {
        require(balanceOf(msg.sender, boostTypeId) > 0, "No boost tokens");
        BoostType storage bt = boostTypes[boostTypeId];
        require(bt.exists, "Invalid boost");
        
        _burn(msg.sender, boostTypeId, 1);
        uint256 expiry = block.timestamp + bt.durationSeconds;
        activeBoosts[msg.sender][boostTypeId] = expiry;
        
        emit BoostActivated(msg.sender, boostTypeId, expiry);
    }
    
    function isBoostActive(address player, uint256 boostTypeId) external view returns (bool) {
        return activeBoosts[player][boostTypeId] > block.timestamp;
    }
    
    function getActiveMultiplier(address player) external view returns (uint256) {
        uint256 totalMult = 10000; // 1x base
        for (uint256 i = 0; i < nextBoostTypeId; i++) {
            if (activeBoosts[player][i] > block.timestamp) {
                totalMult = (totalMult * boostTypes[i].multiplierBp) / 10000;
            }
        }
        return totalMult;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/// @title DiscipleNFT
/// @notice NFT representing a player's disciple (AI trading agent)
contract DiscipleNFT is ERC721, ERC721Enumerable, Ownable {
    using Strings for uint256;
    
    struct Disciple {
        uint256 tokenId;
        string name;
        uint8 specialization; // 0-5 matching the 6 RFBs
        uint256 power;
        uint256 speed;
        uint256 luck;
        uint256 defense;
        uint256 experience;
        uint256 level;
        string meshyUri; // 3D model URI from Meshy.ai
    }
    
    mapping(uint256 => Disciple) public disciples;
    uint256 public nextTokenId;
    string public baseUri;
    
    event DiscipleMinted(uint256 indexed tokenId, address indexed owner, uint8 specialization);
    event DiscipleLeveledUp(uint256 indexed tokenId, uint256 newLevel);
    event DiscipleStatsUpdated(uint256 indexed tokenId);
    
    constructor(string memory _baseUri) ERC721("Coven Disciple", "DISCIPLE") Ownable(msg.sender) {
        baseUri = _baseUri;
    }
    
    function mintDisciple(
        address to,
        string memory name,
        uint8 specialization,
        uint256 power,
        uint256 speed,
        uint256 luck,
        uint256 defense,
        string memory meshyUri
    ) external onlyOwner returns (uint256) {
        require(specialization < 6, "Invalid specialization");
        uint256 tokenId = nextTokenId++;
        
        disciples[tokenId] = Disciple({
            tokenId: tokenId,
            name: name,
            specialization: specialization,
            power: power,
            speed: speed,
            luck: luck,
            defense: defense,
            experience: 0,
            level: 1,
            meshyUri: meshyUri
        });
        
        _safeMint(to, tokenId);
        emit DiscipleMinted(tokenId, to, specialization);
        return tokenId;
    }
    
    function levelUp(uint256 tokenId) external onlyOwner {
        require(_exists(tokenId), "Disciple does not exist");
        Disciple storage d = disciples[tokenId];
        d.level++;
        d.power = (d.power * 110) / 100; // +10%
        d.speed = (d.speed * 110) / 100;
        d.defense = (d.defense * 110) / 100;
        emit DiscipleLeveledUp(tokenId, d.level);
    }
    
    function updateStats(uint256 tokenId, uint256 power, uint256 speed, uint256 luck, uint256 defense) external onlyOwner {
        require(_exists(tokenId), "Disciple does not exist");
        Disciple storage d = disciples[tokenId];
        d.power = power;
        d.speed = speed;
        d.luck = luck;
        d.defense = defense;
        emit DiscipleStatsUpdated(tokenId);
    }
    
    function addExperience(uint256 tokenId, uint256 xp) external onlyOwner {
        require(_exists(tokenId), "Disciple does not exist");
        Disciple storage d = disciples[tokenId];
        d.experience += xp;
        // Level up formula: level^1.5 * 1000 XP needed
        uint256 xpNeeded = (d.level ** 3 * 1000) / 100;
        if (d.experience >= xpNeeded) {
            d.level++;
            d.experience -= xpNeeded;
            emit DiscipleLeveledUp(tokenId, d.level);
        }
    }
    
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_exists(tokenId), "URI query for nonexistent token");
        return string(abi.encodePacked(baseUri, tokenId.toString(), ".json"));
    }
    
    function setBaseUri(string memory _baseUri) external onlyOwner {
        baseUri = _baseUri;
    }
    
    function _exists(uint256 tokenId) internal view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }
    
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721Enumerable) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}

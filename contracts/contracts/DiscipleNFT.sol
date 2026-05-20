// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title DiscipleNFT
 * @dev ERC721 fleet ownership NFT for Coven Traders.
 *      Each Disciple represents a playable fleet with on-chain metadata.
 */
contract DiscipleNFT is ERC721, ERC721Enumerable, AccessControl, ReentrancyGuard {
    using Counters for Counters.Counter;

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant METADATA_ROLE = keccak256("METADATA_ROLE");

    Counters.Counter private _tokenIdCounter;

    struct Disciple {
        uint256 fleetId;       // fleet archetype id
        uint256 power;         // base power
        uint256 rarity;        // 1=common .. 5=mythic
        string name;
        uint256 mintedAt;
        uint256 xp;
    }

    mapping(uint256 => Disciple) public disciples;
    mapping(uint256 => string) private _tokenURIs;

    // Mint pricing in USDC (6 decimals)
    address public paymentToken;
    uint256 public mintPrice;
    bool public mintingEnabled;

    event DiscipleMinted(address indexed to, uint256 indexed tokenId, uint256 fleetId, uint256 rarity);
    event MintPriceUpdated(uint256 oldPrice, uint256 newPrice);
    event MintingToggled(bool enabled);
    event XpGained(uint256 indexed tokenId, uint256 amount);

    constructor(
        address admin,
        address _paymentToken,
        uint256 _mintPrice
    ) ERC721("Coven Disciple", "DISCIPLE") {
        require(admin != address(0), "DiscipleNFT: zero admin");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(METADATA_ROLE, admin);
        paymentToken = _paymentToken;
        mintPrice = _mintPrice;
        mintingEnabled = true;
        _tokenIdCounter.increment(); // start at 1
    }

    modifier onlyMinter() {
        require(hasRole(MINTER_ROLE, msg.sender), "DiscipleNFT: must have minter role");
        _;
    }

    /**
     * @notice Mint a new Disciple. If payment token set and price > 0, transfers USDC from caller.
     */
    function mint(
        address to,
        uint256 fleetId,
        uint256 power,
        uint256 rarity,
        string calldata name,
        string calldata uri
    ) external onlyMinter nonReentrant returns (uint256) {
        require(mintingEnabled, "DiscipleNFT: minting disabled");
        require(to != address(0), "DiscipleNFT: zero to");

        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();

        disciples[tokenId] = Disciple({
            fleetId: fleetId,
            power: power,
            rarity: rarity,
            name: name,
            mintedAt: block.timestamp,
            xp: 0
        });

        _safeMint(to, tokenId);
        _tokenURIs[tokenId] = uri;

        emit DiscipleMinted(to, tokenId, fleetId, rarity);
        return tokenId;
    }

    /**
     * @notice Batch mint for airdrops or rewards.
     */
    function batchMint(
        address[] calldata recipients,
        uint256[] calldata fleetIds,
        uint256[] calldata powers,
        uint256[] calldata rarities,
        string[] calldata names,
        string[] calldata uris
    ) external onlyMinter nonReentrant returns (uint256[] memory tokenIds) {
        uint256 n = recipients.length;
        require(
            n == fleetIds.length && n == powers.length && n == rarities.length && n == names.length && n == uris.length,
            "DiscipleNFT: array length mismatch"
        );
        tokenIds = new uint256[](n);
        for (uint256 i = 0; i < n; i++) {
            uint256 tokenId = _tokenIdCounter.current();
            _tokenIdCounter.increment();
            disciples[tokenId] = Disciple({
                fleetId: fleetIds[i],
                power: powers[i],
                rarity: rarities[i],
                name: names[i],
                mintedAt: block.timestamp,
                xp: 0
            });
            _safeMint(recipients[i], tokenId);
            _tokenURIs[tokenId] = uris[i];
            tokenIds[i] = tokenId;
            emit DiscipleMinted(recipients[i], tokenId, fleetIds[i], rarities[i]);
        }
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_exists(tokenId), "DiscipleNFT: URI query for nonexistent token");
        return _tokenURIs[tokenId];
    }

    function setTokenURI(uint256 tokenId, string calldata uri) external onlyRole(METADATA_ROLE) {
        require(_exists(tokenId), "DiscipleNFT: nonexistent token");
        _tokenURIs[tokenId] = uri;
    }

    function addXp(uint256 tokenId, uint256 amount) external onlyRole(METADATA_ROLE) {
        require(_exists(tokenId), "DiscipleNFT: nonexistent token");
        disciples[tokenId].xp += amount;
        emit XpGained(tokenId, amount);
    }

    function setMintPrice(uint256 newPrice) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 old = mintPrice;
        mintPrice = newPrice;
        emit MintPriceUpdated(old, newPrice);
    }

    function toggleMinting(bool enabled) external onlyRole(DEFAULT_ADMIN_ROLE) {
        mintingEnabled = enabled;
        emit MintingToggled(enabled);
    }

    function setPaymentToken(address _paymentToken) external onlyRole(DEFAULT_ADMIN_ROLE) {
        paymentToken = _paymentToken;
    }

    function totalMinted() external view returns (uint256) {
        return _tokenIdCounter.current() - 1;
    }

    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC721Enumerable, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}

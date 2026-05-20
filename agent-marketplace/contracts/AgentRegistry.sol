// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/// @title AgentRegistry
/// @notice NFT-based registry for user-owned AI trading agents
contract AgentRegistry is ERC721, Ownable, ReentrancyGuard {
    IERC20 public usdc;
    
    struct Agent {
        bytes32 agentId;
        address owner;
        string name;
        string specialization;
        uint8 tier; // 1=common, 2=rare, 3=epic, 4=legendary
        uint256 power;
        uint256 speed;
        uint256 winRate; // basis points
        uint256 totalTrades;
        string strategyURI; // IPFS hash of strategy config
        bool isForSale;
        uint256 salePrice;
        bool isForRent;
        uint256 rentPricePerDay;
        address currentRenter;
        uint256 rentalExpiry;
    }
    
    mapping(uint256 => Agent) public agents;
    mapping(bytes32 => uint256) public agentIdToToken;
    uint256 public nextTokenId;
    uint256 public constant PLATFORM_FEE_BP = 500; // 5%
    address public treasury;
    
    event AgentRegistered(uint256 indexed tokenId, bytes32 indexed agentId, address owner, string name);
    event AgentListed(uint256 indexed tokenId, uint256 price, bool isRental);
    event AgentDelisted(uint256 indexed tokenId);
    event AgentPurchased(uint256 indexed tokenId, address buyer, uint256 price);
    event AgentRented(uint256 indexed tokenId, address renter, uint256 days_, uint256 totalPrice);
    event StrategyUpdated(uint256 indexed tokenId, string strategyURI);
    
    constructor(address _usdc, address _treasury) ERC721("Coven Agent", "AGENT") Ownable(msg.sender) {
        usdc = IERC20(_usdc);
        treasury = _treasury;
    }
    
    function registerAgent(
        bytes32 agentId,
        string calldata name,
        string calldata specialization,
        uint8 tier,
        uint256 power,
        uint256 speed,
        string calldata strategyURI
    ) external returns (uint256) {
        require(agentIdToToken[agentId] == 0, "Agent already registered");
        
        uint256 tokenId = nextTokenId++;
        agents[tokenId] = Agent({
            agentId: agentId,
            owner: msg.sender,
            name: name,
            specialization: specialization,
            tier: tier,
            power: power,
            speed: speed,
            winRate: 0,
            totalTrades: 0,
            strategyURI: strategyURI,
            isForSale: false,
            salePrice: 0,
            isForRent: false,
            rentPricePerDay: 0,
            currentRenter: address(0),
            rentalExpiry: 0
        });
        agentIdToToken[agentId] = tokenId;
        
        _mint(msg.sender, tokenId);
        emit AgentRegistered(tokenId, agentId, msg.sender, name);
        return tokenId;
    }
    
    function listForSale(uint256 tokenId, uint256 price) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        Agent storage a = agents[tokenId];
        a.isForSale = true;
        a.salePrice = price;
        a.isForRent = false;
        emit AgentListed(tokenId, price, false);
    }
    
    function listForRent(uint256 tokenId, uint256 pricePerDay) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        Agent storage a = agents[tokenId];
        a.isForRent = true;
        a.rentPricePerDay = pricePerDay;
        a.isForSale = false;
        emit AgentListed(tokenId, pricePerDay, true);
    }
    
    function delist(uint256 tokenId) external {
        require(ownerOf(tokenId) == msg.sender, "Not owner");
        Agent storage a = agents[tokenId];
        a.isForSale = false;
        a.isForRent = false;
        emit AgentDelisted(tokenId);
    }
    
    function purchase(uint256 tokenId) external nonReentrant {
        Agent storage a = agents[tokenId];
        require(a.isForSale, "Not for sale");
        require(a.currentRenter == address(0), "Currently rented");
        
        address seller = ownerOf(tokenId);
        uint256 price = a.salePrice;
        uint256 fee = (price * PLATFORM_FEE_BP) / 10000;
        uint256 sellerReceives = price - fee;
        
        usdc.transferFrom(msg.sender, seller, sellerReceives);
        usdc.transferFrom(msg.sender, treasury, fee);
        
        _transfer(seller, msg.sender, tokenId);
        a.owner = msg.sender;
        a.isForSale = false;
        
        emit AgentPurchased(tokenId, msg.sender, price);
    }
    
    function rent(uint256 tokenId, uint256 days_) external nonReentrant {
        Agent storage a = agents[tokenId];
        require(a.isForRent, "Not for rent");
        require(a.currentRenter == address(0) || block.timestamp > a.rentalExpiry, "Already rented");
        
        uint256 totalPrice = a.rentPricePerDay * days_;
        uint256 fee = (totalPrice * PLATFORM_FEE_BP) / 10000;
        uint256 ownerReceives = totalPrice - fee;
        
        usdc.transferFrom(msg.sender, a.owner, ownerReceives);
        usdc.transferFrom(msg.sender, treasury, fee);
        
        a.currentRenter = msg.sender;
        a.rentalExpiry = block.timestamp + (days_ * 86400);
        
        emit AgentRented(tokenId, msg.sender, days_, totalPrice);
    }
    
    function updateStrategy(uint256 tokenId, string calldata strategyURI) external {
        require(ownerOf(tokenId) == msg.sender || agents[tokenId].currentRenter == msg.sender, "Not authorized");
        agents[tokenId].strategyURI = strategyURI;
        emit StrategyUpdated(tokenId, strategyURI);
    }
    
    function updateStats(uint256 tokenId, uint256 winRate, uint256 totalTrades) external onlyOwner {
        Agent storage a = agents[tokenId];
        a.winRate = winRate;
        a.totalTrades = totalTrades;
    }
    
    function getAgent(uint256 tokenId) external view returns (Agent memory) {
        return agents[tokenId];
    }
    
    function isRented(uint256 tokenId) external view returns (bool) {
        Agent storage a = agents[tokenId];
        return a.currentRenter != address(0) && block.timestamp <= a.rentalExpiry;
    }
}

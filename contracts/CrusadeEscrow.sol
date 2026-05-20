// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title CrusadeEscrow
/// @notice Tournament entry fee escrow with automated prize distribution
contract CrusadeEscrow is ReentrancyGuard, Ownable {
    IERC20 public usdc;
    
    struct Crusade {
        uint256 id;
        uint256 entryFee;
        uint256 prizePool;
        uint256 startTime;
        uint256 endTime;
        address[] participants;
        mapping(address => bool) hasEntered;
        mapping(address => uint256) score;
        bool settled;
        uint256 platformFeeBp; // basis points
    }
    
    mapping(uint256 => Crusade) public crusades;
    uint256 public nextCrusadeId;
    uint256 public constant PLATFORM_FEE_BP = 1000; // 10%
    
    event CrusadeCreated(uint256 indexed id, uint256 entryFee, uint256 startTime);
    event EnteredCrusade(uint256 indexed id, address indexed player, uint256 fee);
    event ScoreSubmitted(uint256 indexed id, address indexed player, uint256 score);
    event CrusadeSettled(uint256 indexed id, address[] winners, uint256[] prizes);
    
    constructor(address _usdc) Ownable(msg.sender) {
        usdc = IERC20(_usdc);
    }
    
    function createCrusade(uint256 entryFee, uint256 duration) external onlyOwner returns (uint256) {
        uint256 id = nextCrusadeId++;
        Crusade storage c = crusades[id];
        c.id = id;
        c.entryFee = entryFee;
        c.startTime = block.timestamp;
        c.endTime = block.timestamp + duration;
        c.platformFeeBp = PLATFORM_FEE_BP;
        emit CrusadeCreated(id, entryFee, c.startTime);
        return id;
    }
    
    function enterCrusade(uint256 crusadeId) external nonReentrant {
        Crusade storage c = crusades[crusadeId];
        require(block.timestamp < c.endTime, "Crusade ended");
        require(!c.hasEntered[msg.sender], "Already entered");
        
        usdc.transferFrom(msg.sender, address(this), c.entryFee);
        c.hasEntered[msg.sender] = true;
        c.participants.push(msg.sender);
        c.prizePool += c.entryFee;
        
        emit EnteredCrusade(crusadeId, msg.sender, c.entryFee);
    }
    
    function submitScore(uint256 crusadeId, address player, uint256 score) external onlyOwner {
        Crusade storage c = crusades[crusadeId];
        require(c.hasEntered[player], "Not a participant");
        c.score[player] = score;
        emit ScoreSubmitted(crusadeId, player, score);
    }
    
    function settleCrusade(uint256 crusadeId, address[] calldata winners, uint256[] calldata prizes) external onlyOwner nonReentrant {
        Crusade storage c = crusades[crusadeId];
        require(block.timestamp >= c.endTime, "Crusade not ended");
        require(!c.settled, "Already settled");
        require(winners.length == prizes.length, "Length mismatch");
        
        uint256 totalPrizes;
        for (uint i = 0; i < prizes.length; i++) {
            totalPrizes += prizes[i];
        }
        
        uint256 platformFee = (c.prizePool * c.platformFeeBp) / 10000;
        uint256 available = c.prizePool - platformFee;
        require(totalPrizes <= available, "Prizes exceed pool");
        
        c.settled = true;
        
        // Transfer prizes
        for (uint i = 0; i < winners.length; i++) {
            if (prizes[i] > 0) {
                usdc.transfer(winners[i], prizes[i]);
            }
        }
        
        // Platform fee stays in contract
        emit CrusadeSettled(crusadeId, winners, prizes);
    }
    
    function withdrawPlatformFees() external onlyOwner {
        uint256 balance = usdc.balanceOf(address(this));
        // Only withdraw excess beyond active prize pools
        usdc.transfer(owner(), balance);
    }
    
    function getParticipants(uint256 crusadeId) external view returns (address[] memory) {
        return crusades[crusadeId].participants;
    }
}

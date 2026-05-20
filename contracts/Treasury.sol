// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/// @title Treasury
/// @notice Protocol treasury for fee collection and yield distribution
contract Treasury is Ownable, ReentrancyGuard {
    IERC20 public usdc;
    IERC20 public usyc; // yield-bearing token
    
    uint256 public totalStaked;
    mapping(address => uint256) public stakes;
    mapping(address => uint256) public rewardDebt;
    uint256 public accRewardPerShare;
    uint256 public platformRevenue;
    
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);
    event RewardsClaimed(address indexed user, uint256 amount);
    event RevenueDistributed(uint256 amount);
    
    constructor(address _usdc, address _usyc) Ownable(msg.sender) {
        usdc = IERC20(_usdc);
        usyc = IERC20(_usyc);
    }
    
    function stake(uint256 amount) external nonReentrant {
        usdc.transferFrom(msg.sender, address(this), amount);
        
        if (stakes[msg.sender] > 0) {
            uint256 pending = (stakes[msg.sender] * accRewardPerShare) / 1e12 - rewardDebt[msg.sender];
            if (pending > 0) {
                usdc.transfer(msg.sender, pending);
            }
        }
        
        totalStaked += amount;
        stakes[msg.sender] += amount;
        rewardDebt[msg.sender] = (stakes[msg.sender] * accRewardPerShare) / 1e12;
        
        emit Staked(msg.sender, amount);
    }
    
    function unstake(uint256 amount) external nonReentrant {
        require(stakes[msg.sender] >= amount, "Insufficient stake");
        
        uint256 pending = (stakes[msg.sender] * accRewardPerShare) / 1e12 - rewardDebt[msg.sender];
        if (pending > 0) {
            usdc.transfer(msg.sender, pending);
        }
        
        totalStaked -= amount;
        stakes[msg.sender] -= amount;
        rewardDebt[msg.sender] = (stakes[msg.sender] * accRewardPerShare) / 1e12;
        
        usdc.transfer(msg.sender, amount);
        emit Unstaked(msg.sender, amount);
    }
    
    function distributeRevenue(uint256 amount) external onlyOwner {
        usdc.transferFrom(msg.sender, address(this), amount);
        platformRevenue += amount;
        if (totalStaked > 0) {
            accRewardPerShare += (amount * 1e12) / totalStaked;
        }
        emit RevenueDistributed(amount);
    }
    
    function claimRewards() external nonReentrant {
        uint256 pending = (stakes[msg.sender] * accRewardPerShare) / 1e12 - rewardDebt[msg.sender];
        require(pending > 0, "No rewards");
        rewardDebt[msg.sender] = (stakes[msg.sender] * accRewardPerShare) / 1e12;
        usdc.transfer(msg.sender, pending);
        emit RewardsClaimed(msg.sender, pending);
    }
    
    function pendingRewards(address user) external view returns (uint256) {
        return (stakes[user] * accRewardPerShare) / 1e12 - rewardDebt[user];
    }
}

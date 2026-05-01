// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/// @title AETHER-SCORE Integration Staking
/// @notice Simple contract where protocols stake NCRD to unlock integration tiers.
contract AETHER-SCOREStaking is Ownable {
    IERC20 public immutable ncrd;

    struct StakeInfo {
        uint256 amount;
        uint64 lastUpdated;
    }

    mapping(address => StakeInfo) public stakes;

    event Staked(address indexed staker, uint256 amount);
    event Unstaked(address indexed staker, uint256 amount);

    constructor(address ncrdToken, address owner_) Ownable(owner_) {
        require(ncrdToken != address(0), "Invalid NCRD");
        ncrd = IERC20(ncrdToken);
    }

    /// @notice Stake NCRD tokens to increase your integration tier.
    function stake(uint256 amount) external {
        require(amount > 0, "Amount=0");

        ncrd.transferFrom(msg.sender, address(this), amount);

        StakeInfo storage s = stakes[msg.sender];
        s.amount += amount;
        s.lastUpdated = uint64(block.timestamp);

        emit Staked(msg.sender, amount);
    }

    /// @notice Unstake NCRD tokens.
    function unstake(uint256 amount) external {
        StakeInfo storage s = stakes[msg.sender];
        require(amount > 0 && amount <= s.amount, "Invalid amount");

        s.amount -= amount;
        s.lastUpdated = uint64(block.timestamp);

        ncrd.transfer(msg.sender, amount);

        emit Unstaked(msg.sender, amount);
    }

    /// @notice Returns integration tier based on staked amount.
    /// @param staker Address to check tier for
    /// @return Tier level: 0 = none, 1 = Bronze, 2 = Silver, 3 = Gold
    /// @dev Thresholds: Bronze (500+), Silver (2,000+), Gold (10,000+)
    function integrationTier(address staker) external view returns (uint8) {
        uint256 amt = stakes[staker].amount;

        if (amt >= 10_000 ether) return 3; // Gold
        if (amt >= 2_000 ether) return 2;  // Silver
        if (amt >= 500 ether) return 1;    // Bronze
        return 0;
    }

    /// @notice Returns the staked amount for a given address
    /// @param user Address to check staked amount for
    /// @return The amount of NCRD tokens staked by the user
    function stakedAmount(address user) external view returns (uint256) {
        return stakes[user].amount;
    }
}



// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/utils/PausableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "./libraries/CircuitBreaker.sol";
import "./errors/CustomErrors.sol";

/// @title AETHER-SCORE Integration Staking V2
/// @notice Upgradeable staking contract with gas optimizations, pausable, circuit breakers
contract AETHER-SCOREStakingV2 is
    Initializable,
    AccessControlUpgradeable,
    PausableUpgradeable,
    UUPSUpgradeable
{
    using CircuitBreaker for CircuitBreaker.RateLimit;
    using CircuitBreaker for mapping(address => CircuitBreaker.RateLimit);

    // Roles
    bytes32 public constant STAKING_ADMIN_ROLE = keccak256("STAKING_ADMIN_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");
    bytes32 public constant CIRCUIT_BREAKER_ROLE = keccak256("CIRCUIT_BREAKER_ROLE");

    IERC20 public ncrd;

    // Gas optimization: Pack struct efficiently
    struct StakeInfo {
        uint128 amount; // Reduced from uint256 (enough for most tokens)
        uint64 lastUpdated; // Timestamp
        // Packed into 1 slot: 128 + 64 = 192 bits
    }

    mapping(address => StakeInfo) public stakes;

    // Circuit breaker state
    mapping(address => CircuitBreaker.RateLimit) private _rateLimits;
    CircuitBreaker.CircuitBreakerConfig public circuitBreakerConfig;

    // Enhanced events
    event Staked(
        address indexed staker,
        uint256 amount,
        uint256 totalStaked,
        uint256 timestamp,
        uint256 blockNumber
    );
    event Unstaked(
        address indexed staker,
        uint256 amount,
        uint256 remainingStaked,
        uint256 timestamp,
        uint256 blockNumber
    );
    event CircuitBreakerConfigUpdated(
        uint256 maxOperationsPerWindow,
        uint256 timeWindow,
        uint256 maxAmount,
        bool enabled
    );

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /// @notice Initialize the contract
    function initialize(address ncrdToken, address admin) public initializer {
        __AccessControl_init();
        __Pausable_init();
        __UUPSUpgradeable_init();

        if (ncrdToken == address(0)) revert InvalidNCRDToken();
        ncrd = IERC20(ncrdToken);

        _grantRole(DEFAULT_ADMIN_ROLE, admin);

        // Default circuit breaker config
        circuitBreakerConfig = CircuitBreaker.CircuitBreakerConfig({
            maxOperationsPerWindow: 20, // 20 operations per hour
            timeWindow: 3600, // 1 hour
            maxAmount: 1_000_000 * 1e18, // Max 1M tokens per stake
            enabled: true
        });
    }

    /// @notice Stake NCRD tokens to increase your integration tier.
    function stake(uint256 amount) external whenNotPaused {
        if (amount == 0) revert InvalidAmount();

        // Circuit breaker checks
        if (circuitBreakerConfig.enabled) {
            _rateLimits.checkLimits(circuitBreakerConfig, msg.sender, amount);
        }

        ncrd.transferFrom(msg.sender, address(this), amount);

        StakeInfo storage s = stakes[msg.sender];
        uint256 newTotal = uint256(s.amount) + amount;
        // Check for overflow (though unlikely with uint128)
        if (newTotal > type(uint128).max) revert("Stake amount too large");

        s.amount = uint128(newTotal);
        s.lastUpdated = uint64(block.timestamp);

        emit Staked(msg.sender, amount, newTotal, block.timestamp, block.number);
    }

    /// @notice Unstake NCRD tokens.
    function unstake(uint256 amount) external whenNotPaused {
        StakeInfo storage s = stakes[msg.sender];
        uint256 currentAmount = uint256(s.amount);

        if (amount == 0 || amount > currentAmount) {
            revert InsufficientStake(amount, currentAmount);
        }

        // Circuit breaker checks
        if (circuitBreakerConfig.enabled) {
            _rateLimits.checkRateLimit(circuitBreakerConfig, msg.sender);
        }

        s.amount = uint128(currentAmount - amount);
        s.lastUpdated = uint64(block.timestamp);

        ncrd.transfer(msg.sender, amount);

        emit Unstaked(
            msg.sender,
            amount,
            currentAmount - amount,
            block.timestamp,
            block.number
        );
    }

    /// @notice Returns integration tier based on staked amount.
    /// @param staker Address to check tier for
    /// @return Tier level: 0 = none, 1 = Bronze, 2 = Silver, 3 = Gold
    /// @dev Thresholds: Bronze (500+), Silver (2,000+), Gold (10,000+)
    function integrationTier(address staker) external view returns (uint8) {
        uint256 amt = uint256(stakes[staker].amount);

        if (amt >= 10_000 ether) return 3; // Gold
        if (amt >= 2_000 ether) return 2; // Silver
        if (amt >= 500 ether) return 1; // Bronze
        return 0;
    }

    /// @notice Returns the staked amount for a given address
    function stakedAmount(address user) external view returns (uint256) {
        return uint256(stakes[user].amount);
    }

    // ========= Pausable Functions =========

    /// @notice Pause the contract
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    /// @notice Unpause the contract
    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    // ========= Circuit Breaker Functions =========

    /// @notice Update circuit breaker configuration
    function setCircuitBreakerConfig(
        uint256 maxOperationsPerWindow,
        uint256 timeWindow,
        uint256 maxAmount,
        bool enabled
    ) external onlyRole(CIRCUIT_BREAKER_ROLE) {
        circuitBreakerConfig = CircuitBreaker.CircuitBreakerConfig({
            maxOperationsPerWindow: maxOperationsPerWindow,
            timeWindow: timeWindow,
            maxAmount: maxAmount,
            enabled: enabled
        });
        emit CircuitBreakerConfigUpdated(maxOperationsPerWindow, timeWindow, maxAmount, enabled);
    }

    // ========= UUPS Upgrade Functions =========

    /// @notice Authorize upgrade
    function _authorizeUpgrade(address newImplementation) internal override onlyRole(UPGRADER_ROLE) {}
}



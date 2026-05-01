// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "../errors/CustomErrors.sol";

/// @title CircuitBreaker
/// @notice Library for implementing rate limiting and amount limiting circuit breakers
library CircuitBreaker {
    struct RateLimit {
        uint256 count;
        uint256 windowStart;
    }

    struct CircuitBreakerConfig {
        uint256 maxOperationsPerWindow; // Max operations per time window
        uint256 timeWindow; // Time window in seconds
        uint256 maxAmount; // Max amount per operation
        bool enabled; // Whether circuit breaker is enabled
    }

    /// @notice Check rate limit for an address
    /// @param rateLimits Mapping of address to rate limit data
    /// @param config Circuit breaker configuration
    /// @param account Address to check
    function checkRateLimit(
        mapping(address => RateLimit) storage rateLimits,
        CircuitBreakerConfig memory config,
        address account
    ) internal {
        if (!config.enabled) return;

        RateLimit storage limit = rateLimits[account];
        uint256 currentWindow = block.timestamp / config.timeWindow;

        if (limit.windowStart != currentWindow) {
            // New window, reset count
            limit.windowStart = currentWindow;
            limit.count = 0;
        }

        limit.count++;
        if (limit.count > config.maxOperationsPerWindow) {
            revert RateLimitExceeded(account, config.maxOperationsPerWindow, limit.count);
        }
    }

    /// @notice Check amount limit
    /// @param config Circuit breaker configuration
    /// @param amount Amount to check
    function checkAmountLimit(
        CircuitBreakerConfig memory config,
        uint256 amount
    ) internal pure {
        if (!config.enabled) return;
        if (config.maxAmount > 0 && amount > config.maxAmount) {
            revert AmountLimitExceeded(amount, config.maxAmount);
        }
    }

    /// @notice Check both rate and amount limits
    /// @param rateLimits Mapping of address to rate limit data
    /// @param config Circuit breaker configuration
    /// @param account Address to check
    /// @param amount Amount to check
    function checkLimits(
        mapping(address => RateLimit) storage rateLimits,
        CircuitBreakerConfig memory config,
        address account,
        uint256 amount
    ) internal {
        checkRateLimit(rateLimits, config, account);
        checkAmountLimit(config, amount);
    }
}


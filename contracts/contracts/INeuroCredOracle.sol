// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IAETHER-SCOREOracle
/// @notice Interface for QIE Oracle integration
/// @dev Compatible with Chainlink-style oracle contracts
interface IAETHER-SCOREOracle {
    /// @notice Returns the latest price answer
    /// @return The latest price with decimals applied (e.g., price * 10^decimals)
    function latestAnswer() external view returns (int256);

    /// @notice Returns the number of decimals for the price
    /// @return The number of decimals (typically 8 or 18)
    function decimals() external view returns (uint8);
}



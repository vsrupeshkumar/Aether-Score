// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IAETHER-SCOREScore.sol";

/// @title DemoLender
/// @notice Demo lending contract that uses AETHER-SCORE scores to determine LTV
/// @dev This is a demonstration contract showing how DeFi protocols can integrate AETHER-SCORE
contract DemoLender {
    /// @notice Reference to the AETHER-SCORE credit passport contract
    IAETHER-SCOREScore public immutable AETHER-SCORE;

    /// @notice Emitted when LTV is queried for a user
    event LTVQueried(address indexed user, uint256 ltvBps, uint8 riskBand);

    /// @notice Constructor
    /// @param AETHER-SCOREContract Address of the CreditPassportNFT contract
    constructor(address AETHER-SCOREContract) {
        require(AETHER-SCOREContract != address(0), "Invalid AETHER-SCORE address");
        AETHER-SCORE = IAETHER-SCOREScore(AETHER-SCOREContract);
    }

    /// @notice Get the Loan-to-Value (LTV) ratio for a user based on their credit score
    /// @param user Address of the borrower
    /// @return ltvBps LTV in basis points (e.g., 7000 = 70%)
    /// @dev Risk band mapping:
    ///      - Band 1 (Low risk): 70% LTV
    ///      - Band 2 (Medium risk): 50% LTV
    ///      - Band 3 (High risk): 30% LTV
    ///      - No passport (band 0): 0% LTV
    function getLTV(address user) external view returns (uint256 ltvBps) {
        IAETHER-SCOREScore.ScoreView memory scoreView = AETHER-SCORE.getScore(user);

        // Map risk band to LTV in basis points
        if (scoreView.riskBand == 1) {
            ltvBps = 7000; // 70%
        } else if (scoreView.riskBand == 2) {
            ltvBps = 5000; // 50%
        } else if (scoreView.riskBand == 3) {
            ltvBps = 3000; // 30%
        } else {
            ltvBps = 0; // No passport or unknown risk
        }

        return ltvBps;
    }

    /// @notice Calculate maximum borrowable amount for a given collateral value
    /// @param user Address of the borrower
    /// @param collateralValue Value of collateral in wei (or token units)
    /// @return maxBorrow Maximum amount that can be borrowed
    function calculateMaxBorrow(address user, uint256 collateralValue) external view returns (uint256 maxBorrow) {
        uint256 ltvBps = this.getLTV(user);
        return (collateralValue * ltvBps) / 10000;
    }
}



// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

// Gas-efficient custom errors for AETHER-SCORE contracts

// CreditPassportNFT errors
error InvalidUser();
error ScoreTooHigh(uint16 score);
error InvalidRiskBand(uint8 riskBand);
error NoPassport();
error SoulboundNonTransferable();

// Circuit Breaker errors
error RateLimitExceeded(address account, uint256 limit, uint256 current);
error AmountLimitExceeded(uint256 amount, uint256 limit);
error CircuitBreakerTriggered(string reason);

// Staking errors
error InvalidAmount();
error InsufficientStake(uint256 requested, uint256 available);
error InvalidNCRDToken();

// Lending errors
error OnlyBorrower();
error OfferExpired(uint256 expiry, uint256 current);
error NonceAlreadyUsed(uint256 nonce);
error InvalidAISignature();
error InsufficientCollateral(uint256 required, uint256 provided);
error LoanAlreadyRepaid();
// LoanLiquidated removed - using string error to avoid conflict with event
error InsufficientRepayment(uint256 required, uint256 provided);
error InvalidSigner();

// Access control errors (OpenZeppelin provides AccessControlError, but we define for clarity)
error UnauthorizedRole(bytes32 role, address account);

// Pausable errors
error ContractPaused();
error ContractNotPaused();



// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/utils/PausableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./IAETHER-SCOREScore.sol";
import "./libraries/CircuitBreaker.sol";
import "./errors/CustomErrors.sol";

/// @title LendingVault V2
/// @notice Upgradeable lending vault with gas optimizations, pausable, circuit breakers
contract LendingVaultV2 is
    Initializable,
    AccessControlUpgradeable,
    PausableUpgradeable,
    UUPSUpgradeable
{
    using CircuitBreaker for CircuitBreaker.RateLimit;
    using CircuitBreaker for mapping(address => CircuitBreaker.RateLimit);

    // Roles
    bytes32 public constant LENDING_ADMIN_ROLE = keccak256("LENDING_ADMIN_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");
    bytes32 public constant CIRCUIT_BREAKER_ROLE = keccak256("CIRCUIT_BREAKER_ROLE");

    IAETHER-SCOREScore public AETHER-SCORE;

    /// @notice Address authorized to sign loan offers (AI backend)
    address public aiSigner;

    /// @notice EIP-712 domain separator
    bytes32 public DOMAIN_SEPARATOR;

    /// @notice EIP-712 type hash for LoanOffer
    bytes32 public constant LOAN_OFFER_TYPEHASH = keccak256(
        "LoanOffer(address borrower,uint256 amount,uint256 collateralAmount,uint256 interestRate,uint256 duration,uint256 nonce,uint256 expiry)"
    );

    struct LoanOffer {
        address borrower;
        uint256 amount;
        uint256 collateralAmount;
        uint256 interestRate; // in basis points
        uint256 duration; // in seconds
        uint256 nonce;
        uint256 expiry;
    }

    // Gas optimization: Pack struct efficiently
    struct Loan {
        address borrower;
        uint128 principal; // Reduced from uint256
        uint128 collateralAmount; // Reduced from uint256
        uint64 interestRate; // Reduced from uint256 (basis points fit in uint64)
        uint64 startTime; // Reduced from uint256
        uint32 duration; // Reduced from uint256 (fits in uint32 for reasonable durations)
        bool repaid;
        bool liquidated;
        // Packed efficiently
    }

    /// @notice Mapping of loan ID to Loan struct
    mapping(uint256 => Loan) public loans;

    /// @notice Mapping of borrower to nonce to prevent replay attacks
    mapping(address => mapping(uint256 => bool)) public usedNonces;

    /// @notice Total number of loans created
    uint256 public loanCount;

    /// @notice Native token (QIE) for loans
    address public loanToken;

    // Circuit breaker state
    mapping(address => CircuitBreaker.RateLimit) private _rateLimits;
    CircuitBreaker.CircuitBreakerConfig public circuitBreakerConfig;

    // Enhanced events
    event LoanCreated(
        uint256 indexed loanId,
        address indexed borrower,
        uint256 amount,
        uint256 collateralAmount,
        uint256 interestRate,
        uint256 timestamp,
        uint256 blockNumber
    );
    event LoanRepaid(
        uint256 indexed loanId,
        address indexed borrower,
        uint256 totalRepaid,
        uint256 timestamp,
        uint256 blockNumber
    );
    event LoanLiquidatedEvent(
        uint256 indexed loanId,
        address indexed borrower,
        uint256 timestamp,
        uint256 blockNumber
    );
    event AISignerUpdated(
        address indexed oldSigner,
        address indexed newSigner,
        uint256 timestamp
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
    function initialize(
        address _AETHER-SCORE,
        address _loanToken,
        address _aiSigner,
        address admin
    ) public initializer {
        __AccessControl_init();
        __Pausable_init();
        __UUPSUpgradeable_init();

        if (_AETHER-SCORE == address(0)) revert("Invalid AETHER-SCORE");
        if (_aiSigner == address(0)) revert InvalidSigner();

        AETHER-SCORE = IAETHER-SCOREScore(_AETHER-SCORE);
        loanToken = _loanToken;
        aiSigner = _aiSigner;

        _grantRole(DEFAULT_ADMIN_ROLE, admin);

        // EIP-712 domain separator
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256(
                    "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
                ),
                keccak256(bytes("NeuroLend LendingVault")),
                keccak256(bytes("1")),
                block.chainid,
                address(this)
            )
        );

        // Default circuit breaker config
        circuitBreakerConfig = CircuitBreaker.CircuitBreakerConfig({
            maxOperationsPerWindow: 10, // 10 loans per hour
            timeWindow: 3600, // 1 hour
            maxAmount: 100_000 * 1e18, // Max 100K tokens per loan
            enabled: true
        });
    }

    /// @notice Set the AI signer address
    function setAISigner(address _aiSigner) external onlyRole(LENDING_ADMIN_ROLE) {
        if (_aiSigner == address(0)) revert InvalidSigner();
        address oldSigner = aiSigner;
        aiSigner = _aiSigner;
        emit AISignerUpdated(oldSigner, _aiSigner, block.timestamp);
    }

    /// @notice Create a loan with AI-signed offer
    function createLoan(
        LoanOffer memory offer,
        bytes memory aiSignature
    ) external payable whenNotPaused returns (uint256 loanId) {
        if (msg.sender != offer.borrower) revert OnlyBorrower();
        if (block.timestamp >= offer.expiry) revert OfferExpired(offer.expiry, block.timestamp);
        if (usedNonces[offer.borrower][offer.nonce]) revert NonceAlreadyUsed(offer.nonce);
        if (offer.amount == 0) revert("Amount must be > 0");
        if (offer.collateralAmount == 0) revert("Collateral must be > 0");

        // Circuit breaker checks
        if (circuitBreakerConfig.enabled) {
            _rateLimits.checkLimits(circuitBreakerConfig, msg.sender, offer.amount);
        }

        // Verify AI signature
        if (!verifyAISignature(offer, aiSignature)) revert InvalidAISignature();

        // Check borrower has sufficient collateral
        if (msg.value < offer.collateralAmount) {
            revert InsufficientCollateral(offer.collateralAmount, msg.value);
        }

        // Mark nonce as used
        usedNonces[offer.borrower][offer.nonce] = true;

        // Create loan
        loanId = loanCount++;
        loans[loanId] = Loan({
            borrower: offer.borrower,
            principal: uint128(offer.amount),
            collateralAmount: uint128(offer.collateralAmount),
            interestRate: uint64(offer.interestRate),
            startTime: uint64(block.timestamp),
            duration: uint32(offer.duration),
            repaid: false,
            liquidated: false
        });

        // Transfer loan amount to borrower
        if (loanToken == address(0)) {
            // Native token (QIE)
            payable(offer.borrower).transfer(offer.amount);
        } else {
            // ERC20 token
            IERC20(loanToken).transfer(offer.borrower, offer.amount);
        }

        emit LoanCreated(
            loanId,
            offer.borrower,
            offer.amount,
            offer.collateralAmount,
            offer.interestRate,
            block.timestamp,
            block.number
        );

        return loanId;
    }

    /// @notice Repay a loan
    function repayLoan(uint256 loanId) external payable whenNotPaused {
        Loan storage loan = loans[loanId];
        if (loan.borrower != msg.sender) revert OnlyBorrower();
        if (loan.repaid) revert LoanAlreadyRepaid();
        if (loan.liquidated) revert("Loan liquidated");

        uint256 totalOwed = calculateTotalOwed(loanId);
        if (msg.value < totalOwed) {
            revert InsufficientRepayment(totalOwed, msg.value);
        }

        loan.repaid = true;

        // Return collateral to borrower
        payable(loan.borrower).transfer(loan.collateralAmount);

        // Return excess payment
        if (msg.value > totalOwed) {
            payable(loan.borrower).transfer(msg.value - totalOwed);
        }

        emit LoanRepaid(loanId, loan.borrower, totalOwed, block.timestamp, block.number);
    }

    /// @notice Calculate total amount owed for a loan (principal + interest)
    function calculateTotalOwed(uint256 loanId) public view returns (uint256) {
        Loan memory loan = loans[loanId];
        if (loan.repaid || loan.liquidated) return 0;

        uint256 elapsed = block.timestamp - uint256(loan.startTime);
        uint256 interest = (uint256(loan.principal) *
            uint256(loan.interestRate) *
            elapsed) / (10000 * 365 days);

        return uint256(loan.principal) + interest;
    }

    /// @notice Verify EIP-712 signature from AI backend
    function verifyAISignature(
        LoanOffer memory offer,
        bytes memory signature
    ) internal view returns (bool) {
        bytes32 structHash = keccak256(
            abi.encode(
                LOAN_OFFER_TYPEHASH,
                offer.borrower,
                offer.amount,
                offer.collateralAmount,
                offer.interestRate,
                offer.duration,
                offer.nonce,
                offer.expiry
            )
        );

        bytes32 hash = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash));

        address signer = recoverSigner(hash, signature);
        return signer == aiSigner;
    }

    /// @notice Recover signer from signature
    function recoverSigner(bytes32 hash, bytes memory signature) internal pure returns (address) {
        if (signature.length != 65) revert("Invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }

        if (v < 27) {
            v += 27;
        }

        if (v != 27 && v != 28) revert("Invalid signature");

        return ecrecover(hash, v, r, s);
    }

    /// @notice Get active loans for a borrower (gas optimized)
    function getBorrowerLoans(address borrower) external view returns (uint256[] memory) {
        uint256 count = 0;
        // First pass: count active loans
        for (uint256 i = 0; i < loanCount; i++) {
            Loan memory loan = loans[i];
            if (loan.borrower == borrower && !loan.repaid && !loan.liquidated) {
                count++;
            }
        }

        // Second pass: populate array
        uint256[] memory result = new uint256[](count);
        uint256 index = 0;
        for (uint256 i = 0; i < loanCount; i++) {
            Loan memory loan = loans[i];
            if (loan.borrower == borrower && !loan.repaid && !loan.liquidated) {
                result[index] = i;
                index++;
            }
        }

        return result;
    }

    /// @notice Deposit liquidity
    function deposit() external payable {
        // Accept deposits to fund loans
    }

    /// @notice Withdraw liquidity (admin only)
    function withdraw(uint256 amount) external onlyRole(LENDING_ADMIN_ROLE) {
        payable(msg.sender).transfer(amount);
    }

    /// @notice Get contract balance
    function getBalance() external view returns (uint256) {
        return address(this).balance;
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



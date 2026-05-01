// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts-upgradeable/token/ERC721/ERC721Upgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/utils/PausableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "./IAETHER-SCOREScore.sol";
import "./libraries/CircuitBreaker.sol";
import "./errors/CustomErrors.sol";

/// @title AETHER-SCORE Credit Passport V2
/// @notice Upgradeable soulbound NFT with gas optimizations, pausable, circuit breakers
contract CreditPassportNFTV2 is
    Initializable,
    ERC721Upgradeable,
    AccessControlUpgradeable,
    PausableUpgradeable,
    UUPSUpgradeable,
    IAETHER-SCOREScore
{
    using CircuitBreaker for CircuitBreaker.RateLimit;
    using CircuitBreaker for mapping(address => CircuitBreaker.RateLimit);

    // Roles
    bytes32 public constant SCORE_UPDATER_ROLE = keccak256("SCORE_UPDATER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");
    bytes32 public constant CIRCUIT_BREAKER_ROLE = keccak256("CIRCUIT_BREAKER_ROLE");

    // Gas optimization: Pack struct into 2 storage slots (was 3)
    struct ScoreData {
        uint16 score;       // 0â€“1000
        uint8 riskBand;     // 0â€“3
        uint64 lastUpdated; // unix timestamp
        // Packed: 16 + 8 + 64 = 88 bits, fits in 2 slots
    }

    /// @dev maps wallet -> tokenId (0 = none)
    mapping(address => uint256) private _passportIdOf;

    /// @dev maps tokenId -> score data
    mapping(uint256 => ScoreData) private _scores;

    /// @dev simple incremental id
    uint256 private _nextId;

    // Circuit breaker state
    mapping(address => CircuitBreaker.RateLimit) private _rateLimits;
    CircuitBreaker.CircuitBreakerConfig public circuitBreakerConfig;

    // Enhanced events
    event PassportMinted(
        address indexed user,
        uint256 indexed tokenId,
        uint256 timestamp,
        uint256 blockNumber
    );
    event ScoreUpdated(
        address indexed user,
        uint256 indexed tokenId,
        uint16 score,
        uint8 riskBand,
        uint64 timestamp,
        uint256 blockNumber,
        uint16 previousScore,
        uint8 previousRiskBand
    );
    event CircuitBreakerConfigUpdated(
        uint256 maxOperationsPerWindow,
        uint256 timeWindow,
        uint256 maxAmount,
        bool enabled
    );
    event CircuitBreakerTriggeredEvent(
        address indexed account,
        string reason,
        uint256 timestamp
    );

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /// @notice Initialize the contract (replaces constructor for upgradeable contracts)
    function initialize(address admin) public initializer {
        __ERC721_init("AETHER-SCORE Credit Passport", "NCCP");
        __AccessControl_init();
        __Pausable_init();
        __UUPSUpgradeable_init();

        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _nextId = 1;

        // Default circuit breaker config
        circuitBreakerConfig = CircuitBreaker.CircuitBreakerConfig({
            maxOperationsPerWindow: 10, // 10 updates per hour
            timeWindow: 3600, // 1 hour
            maxAmount: 200, // Max score change of 200 points
            enabled: true
        });
    }

    // ========= Core Public API =========

    /// @notice Mint a new passport or update existing one for `user`.
    /// @dev Only callable by SCORE_UPDATER_ROLE, checks pause and circuit breakers
    function mintOrUpdate(
        address user,
        uint16 score,
        uint8 riskBand
    ) external whenNotPaused onlyRole(SCORE_UPDATER_ROLE) {
        if (user == address(0)) revert InvalidUser();
        if (score > 1000) revert ScoreTooHigh(score);
        if (riskBand > 3) revert InvalidRiskBand(riskBand);

        // Cache in memory for gas optimization
        uint256 tokenId = _passportIdOf[user];
        
        // Circuit breaker checks
        if (circuitBreakerConfig.enabled) {
            // Check rate limit
            _rateLimits.checkRateLimit(circuitBreakerConfig, user);

            // Check amount limit (score change)
            if (tokenId != 0) {
                ScoreData memory oldData = _scores[tokenId];
                uint256 scoreChange = score > oldData.score
                    ? score - oldData.score
                    : oldData.score - score;
                CircuitBreaker.checkAmountLimit(circuitBreakerConfig, scoreChange);
            }
        }
        uint16 previousScore = 0;
        uint8 previousRiskBand = 0;

        if (tokenId == 0) {
            // First time user â€“ mint new soulbound NFT
            tokenId = _nextId++;
            _passportIdOf[user] = tokenId;
            _safeMint(user, tokenId);
            emit PassportMinted(user, tokenId, block.timestamp, block.number);
        } else {
            // Get previous values for event
            ScoreData memory oldData = _scores[tokenId];
            previousScore = oldData.score;
            previousRiskBand = oldData.riskBand;
        }

        uint64 ts = uint64(block.timestamp);
        _scores[tokenId] = ScoreData({score: score, riskBand: riskBand, lastUpdated: ts});

        emit ScoreUpdated(
            user,
            tokenId,
            score,
            riskBand,
            ts,
            block.number,
            previousScore,
            previousRiskBand
        );
    }

    /// @notice Return passport tokenId for a wallet (0 = none).
    function passportIdOf(address user) external view returns (uint256) {
        return _passportIdOf[user];
    }

    /// @inheritdoc IAETHER-SCOREScore
    function getScore(address user) external view override returns (ScoreView memory) {
        uint256 tokenId = _passportIdOf[user];
        if (tokenId == 0) {
            return ScoreView({score: 0, riskBand: 0, lastUpdated: 0});
        }

        ScoreData memory sd = _scores[tokenId];
        return ScoreView({score: sd.score, riskBand: sd.riskBand, lastUpdated: sd.lastUpdated});
    }

    /// @notice Direct score lookup by tokenId (useful for explorers/UI).
    function getScoreByToken(uint256 tokenId) external view returns (ScoreData memory) {
        if (_ownerOf(tokenId) == address(0)) revert("Nonexistent token");
        return _scores[tokenId];
    }

    // ========= Soulbound Logic =========

    /// @dev Prevent transfers â€“ only allow mint (from 0) and burn (to 0).
    function _update(
        address to,
        uint256 tokenId,
        address auth
    ) internal override returns (address) {
        address from = _ownerOf(tokenId);

        // allow mint (from = 0) and burn (to = 0)
        if (from != address(0) && to != address(0)) {
            revert SoulboundNonTransferable();
        }

        address previousOwner = super._update(to, tokenId, auth);

        // If burning, clear mapping so user can be re-minted in the future if needed.
        if (to == address(0)) {
            if (_passportIdOf[previousOwner] == tokenId) {
                _passportIdOf[previousOwner] = 0;
            }
        }

        return previousOwner;
    }

    // ========= Pausable Functions =========

    /// @notice Pause the contract (emergency stop)
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

    // ========= Admin Functions =========

    /// @notice Burn a passport (admin only)
    function adminBurn(address user) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 tokenId = _passportIdOf[user];
        if (tokenId == 0) revert NoPassport();
        _burn(tokenId);
    }

    /// @notice Sets an address as a score updater
    function setScoreUpdater(address updater, bool enabled) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (enabled) {
            _grantRole(SCORE_UPDATER_ROLE, updater);
        } else {
            _revokeRole(SCORE_UPDATER_ROLE, updater);
        }
    }

    // ========= UUPS Upgrade Functions =========

    /// @notice Authorize upgrade (only UPGRADER_ROLE)
    function _authorizeUpgrade(address newImplementation) internal override onlyRole(UPGRADER_ROLE) {}

    // ========= Required Overrides =========

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721Upgradeable, AccessControlUpgradeable)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}



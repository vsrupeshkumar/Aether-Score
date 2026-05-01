// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./IAETHER-SCOREScore.sol";

/// @title AETHER-SCORE Credit Passport
/// @notice Soulbound NFT that stores AI-generated credit scores on QIE.
contract CreditPassportNFT is ERC721, AccessControl, IAETHER-SCOREScore {
    bytes32 public constant SCORE_UPDATER_ROLE = keccak256("SCORE_UPDATER_ROLE");

    struct ScoreData {
        uint16 score;       // 0â€“1000
        uint8 riskBand;     // 0â€“3 (0 = unknown)
        uint64 lastUpdated; // unix timestamp
    }

    /// @dev maps wallet -> tokenId (0 = none)
    mapping(address => uint256) private _passportIdOf;

    /// @dev maps tokenId -> score data
    mapping(uint256 => ScoreData) private _scores;

    /// @dev simple incremental id
    uint256 private _nextId = 1;

    event PassportMinted(address indexed user, uint256 indexed tokenId);
    event ScoreUpdated(
        address indexed user,
        uint256 indexed tokenId,
        uint16 score,
        uint8 riskBand,
        uint64 timestamp
    );

    constructor(address admin) ERC721("AETHER-SCORE Credit Passport", "NCCP") {
        // admin will usually be your deployer / multisig
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    // ========= Core Public API =========

    /// @notice Mint a new passport or update existing one for `user`.
    /// @dev Only callable by SCORE_UPDATER_ROLE (your backend signer or a scoring contract).
    function mintOrUpdate(
        address user,
        uint16 score,
        uint8 riskBand
    ) external onlyRole(SCORE_UPDATER_ROLE) {
        require(user != address(0), "Invalid user");
        require(score <= 1000, "Score too high");
        require(riskBand <= 3, "Invalid risk band");

        uint256 tokenId = _passportIdOf[user];

        if (tokenId == 0) {
            // First time user â€“ mint new soulbound NFT
            tokenId = _nextId++;
            _passportIdOf[user] = tokenId;
            _safeMint(user, tokenId);
            emit PassportMinted(user, tokenId);
        }

        uint64 ts = uint64(block.timestamp);
        _scores[tokenId] = ScoreData({score: score, riskBand: riskBand, lastUpdated: ts});

        emit ScoreUpdated(user, tokenId, score, riskBand, ts);
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
        require(_ownerOf(tokenId) != address(0), "Nonexistent token");
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
            revert("Soulbound: non-transferable");
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

    // Optional: expose a burn function (only admin)
    function adminBurn(address user) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 tokenId = _passportIdOf[user];
        require(tokenId != 0, "No passport");
        _burn(tokenId);
    }

    // ========= Admin Helpers =========

    /// @notice Sets an address (e.g. backend signer) as a score updater.
    function setScoreUpdater(address updater, bool enabled) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (enabled) {
            _grantRole(SCORE_UPDATER_ROLE, updater);
        } else {
            _revokeRole(SCORE_UPDATER_ROLE, updater);
        }
    }

    // ========= Required Overrides =========

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}



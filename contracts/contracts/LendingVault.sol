// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./IAETHER-SCOREScore.sol";

/// @title LendingVault
/// @notice Lending vault that uses AETHER-SCORE scores and AI-signed offers for personalized loans
/// @dev Uses EIP-712 for signature verification of AI-generated loan offers
contract LendingVault is Ownable {
    IAETHER-SCOREScore public immutable AETHER-SCORE;
    
    /// @notice Address authorized to sign loan offers (AI backend)
    address public aiSigner;
    
    /// @notice EIP-712 domain separator
    bytes32 public immutable DOMAIN_SEPARATOR;
    
    /// @notice EIP-712 type hash for LoanOffer
    bytes32 public constant LOAN_OFFER_TYPEHASH = keccak256(
        "LoanOffer(address borrower,uint256 amount,uint256 collateralAmount,uint256 interestRate,uint256 duration,uint256 nonce,uint256 expiry)"
    );
    
    struct LoanOffer {
        address borrower;
        uint256 amount;
        uint256 collateralAmount;
        uint256 interestRate; // in basis points (e.g., 450 = 4.5%)
        uint256 duration; // in seconds
        uint256 nonce;
        uint256 expiry;
    }
    
    struct Loan {
        address borrower;
        uint256 principal;
        uint256 collateralAmount;
        uint256 interestRate;
        uint256 startTime;
        uint256 duration;
        bool repaid;
        bool liquidated;
    }
    
    /// @notice Mapping of loan ID to Loan struct
    mapping(uint256 => Loan) public loans;
    
    /// @notice Mapping of borrower to nonce to prevent replay attacks
    mapping(address => mapping(uint256 => bool)) public usedNonces;
    
    /// @notice Total number of loans created
    uint256 public loanCount;
    
    /// @notice Native token (QIE) for loans
    address public immutable loanToken;
    
    event LoanCreated(
        uint256 indexed loanId,
        address indexed borrower,
        uint256 amount,
        uint256 collateralAmount,
        uint256 interestRate
    );
    
    event LoanRepaid(uint256 indexed loanId, address indexed borrower, uint256 totalRepaid);
    event LoanLiquidated(uint256 indexed loanId, address indexed borrower);
    event AISignerUpdated(address indexed oldSigner, address indexed newSigner);
    
    constructor(
        address _AETHER-SCORE,
        address _loanToken,
        address _aiSigner,
        address owner_
    ) Ownable(owner_) {
        require(_AETHER-SCORE != address(0), "Invalid AETHER-SCORE");
        // Allow address(0) for native token (QIE)
        // require(_loanToken != address(0), "Invalid loan token");
        require(_aiSigner != address(0), "Invalid AI signer");
        
        AETHER-SCORE = IAETHER-SCOREScore(_AETHER-SCORE);
        loanToken = _loanToken;
        aiSigner = _aiSigner;
        
        // EIP-712 domain separator
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
                keccak256(bytes("NeuroLend LendingVault")),
                keccak256(bytes("1")),
                block.chainid,
                address(this)
            )
        );
    }
    
    /// @notice Set the AI signer address
    function setAISigner(address _aiSigner) external onlyOwner {
        require(_aiSigner != address(0), "Invalid signer");
        address oldSigner = aiSigner;
        aiSigner = _aiSigner;
        emit AISignerUpdated(oldSigner, _aiSigner);
    }
    
    /// @notice Create a loan with AI-signed offer
    /// @param offer The loan offer details
    /// @param aiSignature EIP-712 signature from AI backend
    function createLoan(
        LoanOffer memory offer,
        bytes memory aiSignature
    ) external payable returns (uint256 loanId) {
        require(msg.sender == offer.borrower, "Only borrower can create loan");
        require(block.timestamp < offer.expiry, "Offer expired");
        require(!usedNonces[offer.borrower][offer.nonce], "Nonce already used");
        require(offer.amount > 0, "Amount must be > 0");
        require(offer.collateralAmount > 0, "Collateral must be > 0");
        
        // Verify AI signature
        require(verifyAISignature(offer, aiSignature), "Invalid AI signature");
        
        // Check borrower has sufficient collateral
        require(msg.value >= offer.collateralAmount, "Insufficient collateral");
        
        // Mark nonce as used
        usedNonces[offer.borrower][offer.nonce] = true;
        
        // Create loan
        loanId = loanCount++;
        loans[loanId] = Loan({
            borrower: offer.borrower,
            principal: offer.amount,
            collateralAmount: offer.collateralAmount,
            interestRate: offer.interestRate,
            startTime: block.timestamp,
            duration: offer.duration,
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
            offer.interestRate
        );
        
        return loanId;
    }
    
    /// @notice Repay a loan
    /// @param loanId The ID of the loan to repay
    function repayLoan(uint256 loanId) external payable {
        Loan storage loan = loans[loanId];
        require(loan.borrower == msg.sender, "Not your loan");
        require(!loan.repaid, "Loan already repaid");
        require(!loan.liquidated, "Loan liquidated");
        
        uint256 totalOwed = calculateTotalOwed(loanId);
        require(msg.value >= totalOwed, "Insufficient repayment");
        
        loan.repaid = true;
        
        // Return collateral to borrower
        payable(loan.borrower).transfer(loan.collateralAmount);
        
        // Return excess payment
        if (msg.value > totalOwed) {
            payable(loan.borrower).transfer(msg.value - totalOwed);
        }
        
        emit LoanRepaid(loanId, loan.borrower, totalOwed);
    }
    
    /// @notice Calculate total amount owed for a loan (principal + interest)
    function calculateTotalOwed(uint256 loanId) public view returns (uint256) {
        Loan memory loan = loans[loanId];
        if (loan.repaid || loan.liquidated) return 0;
        
        uint256 elapsed = block.timestamp - loan.startTime;
        uint256 interest = (loan.principal * loan.interestRate * elapsed) / (10000 * 365 days);
        
        return loan.principal + interest;
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
        require(signature.length == 65, "Invalid signature length");
        
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
        
        require(v == 27 || v == 28, "Invalid signature");
        
        return ecrecover(hash, v, r, s);
    }
    
    /// @notice Get active loans for a borrower
    function getBorrowerLoans(address borrower) external view returns (uint256[] memory) {
        uint256[] memory activeLoans = new uint256[](loanCount);
        uint256 count = 0;
        
        for (uint256 i = 0; i < loanCount; i++) {
            if (loans[i].borrower == borrower && !loans[i].repaid && !loans[i].liquidated) {
                activeLoans[count] = i;
                count++;
            }
        }
        
        // Resize array
        uint256[] memory result = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = activeLoans[i];
        }
        
        return result;
    }
    
    /// @notice Deposit liquidity (for demo/testing)
    function deposit() external payable {
        // Accept deposits to fund loans
        // In production, this would have access control
    }
    
    /// @notice Withdraw liquidity (owner only)
    function withdraw(uint256 amount) external onlyOwner {
        payable(owner()).transfer(amount);
    }
    
    /// @notice Get contract balance
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}



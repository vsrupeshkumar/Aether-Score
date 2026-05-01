"""
Score explanation service for generating human-readable explanations of score changes
"""
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class ScoreExplanationService:
    """Service for generating score change explanations"""
    
    # Reason descriptions mapping
    REASON_DESCRIPTIONS = {
        "loan_repayment": "successful loan repayment",
        "staking_boost": "staking boost",
        "oracle_penalty": "oracle volatility penalty",
        "transaction_volume": "transaction volume change",
        "portfolio_diversification": "portfolio diversification improvement",
        "default": "on-chain activity change",
        "initial_score": "initial credit score calculation",
        "score_recalculation": "periodic score recalculation",
    }
    
    @staticmethod
    def generate_explanation(
        old_score: Optional[int],
        new_score: int,
        change_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate human-readable explanation of score change
        
        Args:
            old_score: Previous score (None for first score)
            new_score: New score
            change_reason: Reason for change (e.g., "loan_repayment", "staking_boost")
            metadata: Additional metadata (e.g., {"amount": 100, "tier": "Gold"})
            
        Returns:
            Human-readable explanation string
        """
        if old_score is None:
            return f"Initial credit score calculated: {new_score} points based on on-chain activity analysis."
        
        score_change = new_score - old_score
        
        if score_change == 0:
            return f"Credit score remained at {new_score} points. No significant changes detected."
        
        # Get reason description
        reason_desc = ScoreExplanationService.REASON_DESCRIPTIONS.get(
            change_reason or "default",
            ScoreExplanationService.REASON_DESCRIPTIONS["default"]
        )
        
        # Build explanation based on change direction
        if score_change > 0:
            explanation = f"Score increased by {score_change} points due to {reason_desc}."
            
            # Add metadata details if available
            if metadata:
                details = []
                if "amount" in metadata:
                    details.append(f"amount: {metadata['amount']}")
                if "tier" in metadata:
                    details.append(f"tier: {metadata['tier']}")
                if "boost" in metadata:
                    details.append(f"boost: +{metadata['boost']} points")
                if "penalty" in metadata:
                    details.append(f"penalty: -{metadata['penalty']} points")
                
                if details:
                    explanation += f" ({', '.join(details)})"
        else:
            explanation = f"Score decreased by {abs(score_change)} points due to {reason_desc}."
            
            # Add metadata details if available
            if metadata:
                details = []
                if "penalty" in metadata:
                    details.append(f"penalty: {metadata['penalty']} points")
                if "volatility" in metadata:
                    details.append(f"volatility: {metadata['volatility']}")
                
                if details:
                    explanation += f" ({', '.join(details)})"
        
        explanation += f" New score: {new_score} points."
        
        return explanation
    
    @staticmethod
    def determine_change_reason(
        old_score: Optional[int],
        new_score: int,
        base_score: Optional[int] = None,
        staking_boost: int = 0,
        oracle_penalty: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Determine the primary reason for score change
        
        Args:
            old_score: Previous score
            new_score: New score
            base_score: Base score before boosts/penalties
            staking_boost: Staking boost applied
            oracle_penalty: Oracle penalty applied
            metadata: Additional metadata
            
        Returns:
            Change reason string
        """
        if old_score is None:
            return "initial_score"
        
        # Check if staking boost is the main factor
        if staking_boost > 0 and new_score > old_score:
            return "staking_boost"
        
        # Check if oracle penalty is the main factor
        if oracle_penalty > 0 and new_score < old_score:
            return "oracle_penalty"
        
        # Check metadata for specific reasons
        if metadata:
            if metadata.get("loan_repaid"):
                return "loan_repayment"
            if metadata.get("transaction_volume_change"):
                return "transaction_volume"
            if metadata.get("portfolio_diversified"):
                return "portfolio_diversification"
        
        # Default to recalculation
        return "score_recalculation"


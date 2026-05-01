"""
Score prediction service for predicting score changes based on scenarios
"""
from typing import Dict, Optional, Any
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class ScorePredictorService:
    """Service for predicting score changes based on scenarios"""
    
    # Score impact factors (points per unit)
    IMPACT_FACTORS = {
        "loan_repayment": {
            "base_impact": 20,  # Base points for repaying a loan
            "per_qie": 0.1,  # Additional points per QIE repaid
            "max_impact": 100,  # Maximum impact from single repayment
        },
        "staking": {
            "base_impact": 10,  # Base points for staking
            "per_qie": 0.05,  # Additional points per QIE staked
            "max_impact": 150,  # Maximum impact from staking
            "tier_multipliers": {1: 1.0, 2: 1.5, 3: 2.0},  # Tier multipliers
        },
        "transaction_volume": {
            "base_impact": 5,  # Base points for increased volume
            "per_qie": 0.01,  # Additional points per QIE volume
            "max_impact": 50,
        },
        "portfolio_diversification": {
            "base_impact": 15,  # Base points for diversification
            "max_impact": 75,
        },
    }
    
    @staticmethod
    def predict_score_change(
        current_score: int,
        scenario: str,
        scenario_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict score change based on scenario
        
        Args:
            current_score: Current credit score
            scenario: Scenario type ("loan_repayment", "staking", "transaction_volume", etc.)
            scenario_data: Scenario-specific data (amount, tier, etc.)
            
        Returns:
            Dict with predicted_score, predicted_change, confidence_level, explanation
        """
        scenario_data = scenario_data or {}
        
        # Get impact factors for scenario
        factors = ScorePredictorService.IMPACT_FACTORS.get(
            scenario,
            {"base_impact": 0, "per_qie": 0, "max_impact": 0}
        )
        
        # Calculate predicted change
        predicted_change = factors.get("base_impact", 0)
        
        # Apply scenario-specific calculations
        if scenario == "loan_repayment":
            amount = scenario_data.get("amount", 0)
            if amount > 0:
                per_qie = factors.get("per_qie", 0)
                additional = min(amount * per_qie, factors.get("max_impact", 100) - predicted_change)
                predicted_change = min(predicted_change + additional, factors.get("max_impact", 100))
        
        elif scenario == "staking":
            amount = scenario_data.get("amount", 0)
            tier = scenario_data.get("tier", 1)
            if amount > 0:
                per_qie = factors.get("per_qie", 0)
                tier_multiplier = factors.get("tier_multipliers", {}).get(tier, 1.0)
                additional = min(
                    amount * per_qie * tier_multiplier,
                    factors.get("max_impact", 150) - predicted_change
                )
                predicted_change = min(predicted_change + additional, factors.get("max_impact", 150))
        
        elif scenario == "transaction_volume":
            volume_increase = scenario_data.get("volume_increase", 0)
            if volume_increase > 0:
                per_qie = factors.get("per_qie", 0)
                additional = min(
                    volume_increase * per_qie,
                    factors.get("max_impact", 50) - predicted_change
                )
                predicted_change = min(predicted_change + additional, factors.get("max_impact", 50))
        
        elif scenario == "portfolio_diversification":
            # Simple impact for diversification
            predicted_change = factors.get("base_impact", 15)
        
        # Calculate predicted score (clamped to 0-1000)
        predicted_score = max(0, min(1000, current_score + predicted_change))
        
        # Calculate confidence level based on scenario and data quality
        confidence = ScorePredictorService._calculate_confidence(scenario, scenario_data)
        
        # Generate explanation
        explanation = ScorePredictorService._generate_prediction_explanation(
            scenario, predicted_change, scenario_data
        )
        
        return {
            "predicted_score": int(predicted_score),
            "predicted_change": int(predicted_change),
            "current_score": current_score,
            "confidence_level": confidence,
            "explanation": explanation,
            "scenario": scenario,
        }
    
    @staticmethod
    def _calculate_confidence(scenario: str, scenario_data: Optional[Dict[str, Any]]) -> float:
        """
        Calculate confidence level (0.0 to 1.0) for prediction
        
        Args:
            scenario: Scenario type
            scenario_data: Scenario data
            
        Returns:
            Confidence level between 0.0 and 1.0
        """
        base_confidence = {
            "loan_repayment": 0.85,
            "staking": 0.80,
            "transaction_volume": 0.70,
            "portfolio_diversification": 0.75,
        }.get(scenario, 0.60)
        
        # Adjust confidence based on data quality
        if scenario_data:
            # Higher confidence if amount/data is provided
            if "amount" in scenario_data and scenario_data["amount"] > 0:
                base_confidence += 0.10
            
            # Lower confidence if data is incomplete
            if scenario == "staking" and "tier" not in scenario_data:
                base_confidence -= 0.10
        
        return min(1.0, max(0.0, base_confidence))
    
    @staticmethod
    def _generate_prediction_explanation(
        scenario: str,
        predicted_change: int,
        scenario_data: Optional[Dict[str, Any]]
    ) -> str:
        """Generate explanation for prediction"""
        scenario_data = scenario_data or {}
        
        if predicted_change == 0:
            return "No significant score change predicted for this scenario."
        
        direction = "increase" if predicted_change > 0 else "decrease"
        
        explanations = {
            "loan_repayment": f"Repaying your loan is predicted to {direction} your score by approximately {abs(predicted_change)} points, reflecting improved creditworthiness.",
            "staking": f"Staking tokens is predicted to {direction} your score by approximately {abs(predicted_change)} points, demonstrating commitment to the platform.",
            "transaction_volume": f"Increasing transaction volume is predicted to {direction} your score by approximately {abs(predicted_change)} points, showing active on-chain engagement.",
            "portfolio_diversification": f"Diversifying your portfolio is predicted to {direction} your score by approximately {abs(predicted_change)} points, reducing concentration risk.",
        }
        
        explanation = explanations.get(
            scenario,
            f"This scenario is predicted to {direction} your score by approximately {abs(predicted_change)} points."
        )
        
        # Add details if available
        if scenario_data.get("amount"):
            explanation += f" Amount: {scenario_data['amount']} QIE."
        
        return explanation


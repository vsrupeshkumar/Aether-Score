"""
Score simulator service for "what if" scenario calculations
"""
from typing import Dict, Optional, Any
from utils.logger import get_logger
from services.scoring import ScoringService
from services.staking import StakingService

logger = get_logger(__name__)


class ScoreSimulator:
    """Service for simulating score changes based on scenarios"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.staking_service = StakingService()
    
    async def simulate_score(
        self,
        address: str,
        scenarios: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate score changes based on scenarios
        
        Args:
            address: Wallet address
            scenarios: Dict with scenario parameters:
                - staking_amount: Additional staking amount
                - transaction_count: Additional transaction count
                - loan_repayment: Loan repayment scenario
                - portfolio_value: New portfolio value
        
        Returns:
            Simulated score results
        """
        try:
            # Get current score
            current_score_info = await self.scoring_service.compute_score(address)
            current_score = current_score_info.get('score', 0)
            current_base_score = current_score_info.get('baseScore', 0)
            
            # Calculate simulated score
            simulated_score = current_base_score
            changes = []
            
            # Apply staking scenario
            if scenarios.get('staking_amount'):
                staking_amount = scenarios['staking_amount']
                # Calculate new staking tier
                current_staked = self.staking_service.get_staked_amount(address)
                new_staked = current_staked + staking_amount
                
                # Estimate new tier (simplified calculation)
                if new_staked >= 10000:
                    new_tier = 3
                elif new_staked >= 2000:
                    new_tier = 2
                elif new_staked >= 500:
                    new_tier = 1
                else:
                    new_tier = 0
                
                current_tier = self.staking_service.get_integration_tier(address)
                if new_tier > current_tier:
                    staking_boost = self.staking_service.calculate_staking_boost(new_tier)
                    current_boost = self.staking_service.calculate_staking_boost(current_tier)
                    boost_change = staking_boost - current_boost
                    simulated_score += boost_change
                    changes.append({
                        "type": "staking",
                        "description": f"Stake {staking_amount} NCRD (Tier {current_tier} → {new_tier})",
                        "change": boost_change,
                    })
            
            # Apply transaction scenario
            if scenarios.get('transaction_count'):
                tx_count = scenarios['transaction_count']
                # Estimate score boost from transactions (simplified)
                # Each 10 transactions ≈ 5-10 points (diminishing returns)
                if tx_count >= 50:
                    tx_boost = 50
                elif tx_count >= 20:
                    tx_boost = 30
                elif tx_count >= 10:
                    tx_boost = 15
                else:
                    tx_boost = tx_count * 1.5
                
                simulated_score += tx_boost
                changes.append({
                    "type": "transaction",
                    "description": f"Add {tx_count} transactions",
                    "change": tx_boost,
                })
            
            # Apply loan repayment scenario
            if scenarios.get('loan_repayment'):
                # Repaying loans improves credit history
                repayment_boost = 20  # Simplified: each repaid loan ≈ 20 points
                simulated_score += repayment_boost
                changes.append({
                    "type": "loan_repayment",
                    "description": "Repay outstanding loans",
                    "change": repayment_boost,
                })
            
            # Apply portfolio scenario
            if scenarios.get('portfolio_value'):
                portfolio_value = scenarios['portfolio_value']
                # Estimate portfolio score boost
                if portfolio_value >= 10000:
                    portfolio_boost = 50
                elif portfolio_value >= 5000:
                    portfolio_boost = 30
                elif portfolio_value >= 1000:
                    portfolio_boost = 15
                else:
                    portfolio_boost = portfolio_value / 100
                
                simulated_score += portfolio_boost
                changes.append({
                    "type": "portfolio",
                    "description": f"Increase portfolio to ${portfolio_value}",
                    "change": portfolio_boost,
                })
            
            # Clamp score to valid range
            simulated_score = max(0, min(1000, simulated_score))
            score_change = simulated_score - current_score
            
            return {
                "current_score": current_score,
                "simulated_score": simulated_score,
                "score_change": score_change,
                "scenarios": scenarios,
                "changes": changes,
            }
        except Exception as e:
            logger.error(f"Error simulating score: {e}", exc_info=True)
            return {
                "current_score": 0,
                "simulated_score": 0,
                "score_change": 0,
                "error": str(e),
            }
    
    async def compare_scenarios(
        self,
        address: str,
        scenario_list: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare multiple scenarios
        
        Args:
            address: Wallet address
            scenario_list: List of scenario dicts
        
        Returns:
            Comparison results
        """
        try:
            results = []
            
            for i, scenario in enumerate(scenario_list):
                result = await self.simulate_score(address, scenario)
                results.append({
                    "scenario_id": i + 1,
                    "scenario": scenario,
                    "result": result,
                })
            
            # Sort by simulated score (highest first)
            results.sort(key=lambda x: x['result']['simulated_score'], reverse=True)
            
            return {
                "address": address,
                "scenarios": results,
            }
        except Exception as e:
            logger.error(f"Error comparing scenarios: {e}", exc_info=True)
            return {
                "address": address,
                "error": str(e),
            }


"""
Staking advisor service for optimal staking recommendations
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from utils.logger import get_logger

logger = get_logger(__name__)


class StakingAdvisor:
    """Service for providing staking recommendations"""
    
    # Staking tiers and their benefits
    STAKING_TIERS = [
        {
            "tier": 1,
            "min_amount": Decimal('0'),
            "max_amount": Decimal('1000'),
            "score_boost": 50,
            "apy": 8.0,
        },
        {
            "tier": 2,
            "min_amount": Decimal('1000'),
            "max_amount": Decimal('5000'),
            "score_boost": 150,
            "apy": 10.0,
        },
        {
            "tier": 3,
            "min_amount": Decimal('5000'),
            "max_amount": Decimal('10000'),
            "score_boost": 250,
            "apy": 12.0,
        },
        {
            "tier": 4,
            "min_amount": Decimal('10000'),
            "max_amount": Decimal('999999999'),
            "score_boost": 300,
            "apy": 15.0,
        },
    ]
    
    def calculate_score_boost_curve(
        self,
        amount: Decimal
    ) -> Dict[str, Any]:
        """
        Calculate score boost vs staking amount
        
        Args:
            amount: Staking amount
            
        Returns:
            Score boost curve data
        """
        try:
            # Find tier
            tier = self._get_tier_for_amount(amount)
            
            if not tier:
                return {
                    "amount": float(amount),
                    "score_boost": 0,
                    "tier": 0,
                    "apy": 0.0,
                }
            
            # Calculate boost (simplified linear within tier)
            tier_min = tier['min_amount']
            tier_max = tier['max_amount']
            tier_range = tier_max - tier_min
            
            if tier_range > 0:
                # Linear interpolation within tier
                progress = (amount - tier_min) / tier_range
                # Use previous tier's boost as base
                prev_tier_boost = self._get_previous_tier_boost(tier['tier'])
                boost_range = tier['score_boost'] - prev_tier_boost
                score_boost = prev_tier_boost + (boost_range * progress)
            else:
                score_boost = tier['score_boost']
            
            return {
                "amount": float(amount),
                "score_boost": int(score_boost),
                "tier": tier['tier'],
                "apy": tier['apy'],
                "tier_info": tier,
            }
        except Exception as e:
            logger.error(f"Error calculating score boost curve: {e}", exc_info=True)
            return {
                "amount": float(amount),
                "score_boost": 0,
                "tier": 0,
                "apy": 0.0,
            }
    
    def suggest_staking_amount(
        self,
        target_score_boost: int,
        available_amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Suggest staking amount for target score boost
        
        Args:
            target_score_boost: Target score boost
            available_amount: Available amount to stake (optional)
            
        Returns:
            Staking recommendation dict
        """
        try:
            # Find tier that provides target boost
            target_tier = None
            for tier in self.STAKING_TIERS:
                if tier['score_boost'] >= target_score_boost:
                    target_tier = tier
                    break
            
            if not target_tier:
                # Use highest tier
                target_tier = self.STAKING_TIERS[-1]
            
            # Calculate suggested amount (use min of tier)
            suggested_amount = target_tier['min_amount']
            
            # If available amount is provided, cap suggestion
            if available_amount and suggested_amount > available_amount:
                suggested_amount = available_amount
                # Recalculate boost for actual amount
                curve = self.calculate_score_boost_curve(suggested_amount)
                actual_boost = curve['score_boost']
            else:
                actual_boost = target_tier['score_boost']
            
            return {
                "target_score_boost": target_score_boost,
                "suggested_amount": float(suggested_amount),
                "expected_score_boost": actual_boost,
                "tier": target_tier['tier'],
                "apy": target_tier['apy'],
                "estimated_annual_rewards": float(suggested_amount * Decimal(str(target_tier['apy'])) / Decimal('100')),
                "explanation": f"Staking {suggested_amount} tokens in tier {target_tier['tier']} should provide {actual_boost} points boost",
            }
        except Exception as e:
            logger.error(f"Error suggesting staking amount: {e}", exc_info=True)
            return {}
    
    def calculate_optimal_allocation(
        self,
        total_amount: Decimal
    ) -> Dict[str, Any]:
        """
        Calculate optimal allocation across tiers
        
        Args:
            total_amount: Total amount available for staking
            
        Returns:
            Optimal allocation dict
        """
        try:
            allocation = []
            remaining = total_amount
            total_boost = 0
            weighted_apy = Decimal('0')
            
            # Allocate to highest tier first (best APY and boost)
            for tier in reversed(self.STAKING_TIERS):
                tier_max = tier['max_amount']
                tier_min = tier['min_amount']
                tier_range = tier_max - tier_min
                
                if remaining <= 0:
                    break
                
                # Calculate amount for this tier
                if remaining >= tier_range:
                    # Fill entire tier
                    tier_amount = tier_range
                    remaining -= tier_range
                else:
                    # Partial fill
                    tier_amount = remaining
                    remaining = Decimal('0')
                
                if tier_amount > 0:
                    curve = self.calculate_score_boost_curve(tier_min + tier_amount)
                    allocation.append({
                        "tier": tier['tier'],
                        "amount": float(tier_amount),
                        "score_boost": curve['score_boost'],
                        "apy": tier['apy'],
                    })
                    total_boost += curve['score_boost']
                    weighted_apy += Decimal(str(tier['apy'])) * (tier_amount / total_amount)
            
            return {
                "total_amount": float(total_amount),
                "allocation": allocation,
                "total_score_boost": int(total_boost),
                "weighted_avg_apy": float(weighted_apy),
                "estimated_annual_rewards": float(total_amount * weighted_apy / Decimal('100')),
            }
        except Exception as e:
            logger.error(f"Error calculating optimal allocation: {e}", exc_info=True)
            return {}
    
    def get_tier_benefits(
        self,
        tier: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get benefits for a specific tier
        
        Args:
            tier: Tier number (1-4)
            
        Returns:
            Tier benefits dict
        """
        try:
            tier_info = next((t for t in self.STAKING_TIERS if t['tier'] == tier), None)
            
            if not tier_info:
                return None
            
            return {
                "tier": tier_info['tier'],
                "min_amount": float(tier_info['min_amount']),
                "max_amount": float(tier_info['max_amount']),
                "score_boost": tier_info['score_boost'],
                "apy": tier_info['apy'],
                "benefits": [
                    f"Up to {tier_info['score_boost']} credit score boost",
                    f"{tier_info['apy']}% APY",
                    "Auto-compounding available",
                    "Priority loan offers",
                ],
            }
        except Exception as e:
            logger.error(f"Error getting tier benefits: {e}", exc_info=True)
            return None
    
    def _get_tier_for_amount(self, amount: Decimal) -> Optional[Dict[str, Any]]:
        """Get tier for a given amount"""
        for tier in self.STAKING_TIERS:
            if tier['min_amount'] <= amount < tier['max_amount']:
                return tier
        # Check highest tier
        if amount >= self.STAKING_TIERS[-1]['min_amount']:
            return self.STAKING_TIERS[-1]
        return None
    
    def _get_previous_tier_boost(self, tier: int) -> int:
        """Get score boost from previous tier"""
        if tier <= 1:
            return 0
        
        prev_tier = next((t for t in self.STAKING_TIERS if t['tier'] == tier - 1), None)
        return prev_tier['score_boost'] if prev_tier else 0


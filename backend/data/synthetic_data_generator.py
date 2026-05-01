"""
Synthetic Data Generator

Generates synthetic training data based on current rule-based scores
to bootstrap ML model training when historical data is limited.
"""

import random
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)


class SyntheticDataGenerator:
    """Generate synthetic training data for ML model"""
    
    def __init__(self):
        self.random_seed = 42
        np.random.seed(self.random_seed)
        random.seed(self.random_seed)
    
    def generate_features(self, score_range: tuple = (0, 1000), count: int = 1000) -> List[Dict[str, Any]]:
        """
        Generate synthetic feature vectors
        
        Args:
            score_range: Tuple of (min_score, max_score) for target scores
            count: Number of samples to generate
            
        Returns:
            List of feature dictionaries with target scores
        """
        samples = []
        
        for i in range(count):
            # Generate base features that correlate with creditworthiness
            target_score = random.randint(score_range[0], score_range[1])
            
            # Generate features that correlate with score
            # Higher scores = more activity, better patterns, lower risk
            
            # Transaction patterns (correlate with score)
            tx_count = max(0, int(np.random.normal(target_score / 10, target_score / 20)))
            tx_frequency_daily = max(0.0, np.random.normal(target_score / 100, target_score / 200))
            tx_regularity_score = min(1.0, max(0.0, np.random.normal(0.5 + (target_score / 2000), 0.2)))
            tx_time_of_day_variance = max(0.0, np.random.normal(50 - (target_score / 20), 20))
            tx_weekend_ratio = min(1.0, max(0.0, np.random.normal(0.2, 0.1)))
            tx_gas_efficiency = min(1.0, max(0.0, np.random.normal(0.5 + (target_score / 2000), 0.2)))
            tx_failure_rate = max(0.0, min(1.0, np.random.normal(0.1 - (target_score / 10000), 0.05)))
            
            # Token holdings
            unique_tokens = max(1, int(np.random.normal(5 + (target_score / 200), 3)))
            token_diversity = min(1.0, max(0.0, np.random.normal(0.3 + (target_score / 2000), 0.2)))
            token_concentration = min(1.0, max(0.0, np.random.normal(0.5 - (target_score / 2000), 0.2)))
            token_stability = min(1.0, max(0.0, np.random.normal(0.4 + (target_score / 2500), 0.2)))
            erc20_count = max(0, int(np.random.normal(unique_tokens * 0.8, 2)))
            erc721_count = max(0, int(np.random.normal(unique_tokens * 0.2, 1)))
            stablecoin_ratio = min(1.0, max(0.0, np.random.normal(0.3 + (target_score / 3000), 0.2)))
            
            # DeFi interactions
            defi_interaction_count = max(0, int(np.random.normal(target_score / 50, target_score / 100)))
            dex_swap_count = max(0, int(np.random.normal(defi_interaction_count * 0.6, 2)))
            liquidity_provision_count = max(0, int(np.random.normal(defi_interaction_count * 0.2, 1)))
            yield_farming_count = max(0, int(np.random.normal(defi_interaction_count * 0.2, 1)))
            unique_defi_protocols = max(0, int(np.random.normal(defi_interaction_count / 3, 1)))
            defi_activity_ratio = min(1.0, max(0.0, np.random.normal(0.2 + (target_score / 5000), 0.15)))
            
            # Network features
            unique_contracts = max(0, int(np.random.normal(tx_count / 5, tx_count / 10)))
            unique_addresses = max(0, int(np.random.normal(tx_count / 3, tx_count / 6)))
            address_clustering_score = min(1.0, max(0.0, np.random.normal(0.3 + (target_score / 3000), 0.2)))
            transaction_graph_density = min(1.0, max(0.0, np.random.normal(0.1 + (target_score / 10000), 0.1)))
            reciprocity_score = min(1.0, max(0.0, np.random.normal(0.2 + (target_score / 5000), 0.15)))
            
            # Temporal features
            account_age_days = max(1, int(np.random.normal(180 + (target_score / 5), 100)))
            activity_streak_days = max(1, int(np.random.normal(10 + (target_score / 100), 5)))
            max_inactivity_days = max(0, int(np.random.normal(30 - (target_score / 50), 15)))
            avg_inactivity_days = max(0.0, np.random.normal(10 - (target_score / 200), 5))
            activity_consistency = min(1.0, max(0.0, np.random.normal(0.5 + (target_score / 2000), 0.2)))
            
            # Financial metrics
            total_volume = max(0.0, np.random.normal(target_score * 10, target_score * 5))
            avg_tx_value = max(0.0, np.random.normal(target_score / 10, target_score / 20))
            max_tx_value = max(0.0, np.random.normal(target_score * 2, target_score))
            portfolio_volatility = max(0.0, min(1.0, np.random.normal(0.3 - (target_score / 3000), 0.15)))
            diversification_index = min(1.0, max(0.0, np.random.normal(0.4 + (target_score / 2500), 0.2)))
            
            # Behavioral features
            gas_price_preference = max(0.0, np.random.normal(20000000000, 5000000000))
            tx_timing_preference = min(1.0, max(0.0, np.random.normal(0.5, 0.2)))
            contract_interaction_preference = min(1.0, max(0.0, np.random.normal(0.3 + (target_score / 3000), 0.2)))
            value_distribution_skew = np.random.normal(0.0, 0.5)
            
            sample = {
                # Transaction patterns
                "tx_count": tx_count,
                "tx_frequency_daily": tx_frequency_daily,
                "tx_regularity_score": tx_regularity_score,
                "tx_time_of_day_variance": tx_time_of_day_variance,
                "tx_weekend_ratio": tx_weekend_ratio,
                "tx_gas_efficiency": tx_gas_efficiency,
                "tx_failure_rate": tx_failure_rate,
                
                # Token holdings
                "token_diversity": token_diversity,
                "token_concentration": token_concentration,
                "token_stability": token_stability,
                "unique_tokens": unique_tokens,
                "erc20_count": erc20_count,
                "erc721_count": erc721_count,
                "stablecoin_ratio": stablecoin_ratio,
                
                # DeFi interactions
                "defi_interaction_count": defi_interaction_count,
                "dex_swap_count": dex_swap_count,
                "liquidity_provision_count": liquidity_provision_count,
                "yield_farming_count": yield_farming_count,
                "unique_defi_protocols": unique_defi_protocols,
                "defi_activity_ratio": defi_activity_ratio,
                
                # Network features
                "unique_contracts": unique_contracts,
                "unique_addresses": unique_addresses,
                "address_clustering_score": address_clustering_score,
                "transaction_graph_density": transaction_graph_density,
                "reciprocity_score": reciprocity_score,
                
                # Temporal features
                "account_age_days": account_age_days,
                "activity_streak_days": activity_streak_days,
                "max_inactivity_days": max_inactivity_days,
                "avg_inactivity_days": avg_inactivity_days,
                "activity_consistency": activity_consistency,
                
                # Financial metrics
                "total_volume": total_volume,
                "avg_tx_value": avg_tx_value,
                "max_tx_value": max_tx_value,
                "portfolio_volatility": portfolio_volatility,
                "diversification_index": diversification_index,
                
                # Behavioral features
                "gas_price_preference": gas_price_preference,
                "tx_timing_preference": tx_timing_preference,
                "contract_interaction_preference": contract_interaction_preference,
                "value_distribution_skew": value_distribution_skew,
                
                # Target
                "target_score": target_score,
            }
            
            samples.append(sample)
        
        logger.info(f"Generated {count} synthetic samples")
        return samples
    
    def augment_real_data(self, real_samples: List[Dict[str, Any]], augmentation_factor: float = 0.5) -> List[Dict[str, Any]]:
        """
        Augment real data with synthetic variations
        
        Args:
            real_samples: List of real feature dictionaries
            augmentation_factor: Fraction of synthetic samples to generate per real sample
            
        Returns:
            Augmented dataset
        """
        augmented = []
        
        for sample in real_samples:
            augmented.append(sample)  # Keep original
            
            # Generate variations
            num_variations = max(1, int(len(real_samples) * augmentation_factor / len(real_samples)))
            
            for _ in range(num_variations):
                variation = sample.copy()
                
                # Add small random noise to features
                for key, value in variation.items():
                    if key != "target_score" and isinstance(value, (int, float)):
                        noise = np.random.normal(0, abs(value) * 0.1)
                        if isinstance(value, int):
                            variation[key] = max(0, int(value + noise))
                        else:
                            variation[key] = max(0.0, value + noise)
                
                augmented.append(variation)
        
        logger.info(f"Augmented {len(real_samples)} real samples to {len(augmented)} total samples")
        return augmented


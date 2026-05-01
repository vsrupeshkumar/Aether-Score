"""
ML-Based Scoring Service

Replaces rule-based scoring with ML predictions using trained XGBoost models.
"""

import os
from typing import Dict, Optional, Any
from models.ml_model import MLModel
from services.feature_engineering import FeatureEngineering
from services.staking import StakingService
from services.oracle import QIEOracleService
from data.feature_store import FeatureStore
from utils.logger import get_logger
from utils.metrics import record_score_computation

logger = get_logger(__name__)


class MLScoringService:
    """ML-based credit scoring service"""
    
    def __init__(self, model_version: Optional[str] = None):
        self.model_version = model_version or os.getenv("ML_MODEL_VERSION", "latest")
        self.model: Optional[MLModel] = None
        self.feature_engineering = FeatureEngineering()
        self.staking_service = StakingService()
        self.oracle_service = QIEOracleService()
        self.feature_store = FeatureStore()
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load ML model"""
        try:
            self.model = MLModel()
            success = self.model.load(self.model_version)
            
            if not success:
                logger.warning(f"Could not load model version {self.model_version}, using rule-based fallback")
                self.model = None
            else:
                logger.info(f"Loaded ML model version {self.model_version}")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}", exc_info=True)
            self.model = None
    
    async def compute_score(self, address: str, use_ml: bool = True) -> Dict[str, Any]:
        """
        Compute credit score using ML model
        
        Args:
            address: Wallet address
            use_ml: Whether to use ML model (fallback to rule-based if False or model unavailable)
            
        Returns:
            Score result dictionary
        """
        import time
        start_time = time.time()
        
        try:
            # Extract features
            features = await self.feature_engineering.extract_all_features(address)
            
            if not features:
                logger.warning(f"No features extracted for {address}, using default score")
                return self._default_score_result()
            
            # Store features
            await self.feature_store.store_features(address, features, version="latest")
            
            # Get ML prediction if available
            ml_score = None
            ml_explanation = None
            model_version_used = None
            
            if use_ml and self.model:
                try:
                    ml_score = self.model.predict_single(features)
                    
                    # Get explanation
                    explanation = self.model.explain_prediction(features, top_n=5)
                    top_features = explanation.get("top_features", [])
                    
                    ml_explanation = ", ".join([
                        f"{feat['feature']}: {feat['contribution']:.2f}"
                        for feat in top_features
                    ])
                    
                    model_version_used = self.model.model_version
                    
                except Exception as e:
                    logger.warning(f"ML prediction failed: {e}, falling back to rule-based")
                    ml_score = None
            
            # Fallback to rule-based if ML not available
            if ml_score is None:
                from services.scoring import ScoringService
                rule_based_service = ScoringService()
                rule_result = await rule_based_service.compute_score(address)
                base_score = rule_result.get("score", 500)
                base_risk_band = rule_result.get("riskBand", 2)
                base_explanation = rule_result.get("explanation", "Rule-based scoring")
            else:
                base_score = int(ml_score)
                base_risk_band = self._score_to_risk_band(base_score)
                base_explanation = ml_explanation or "ML-based scoring"
            
            # Apply staking boost
            staking_tier = self.staking_service.get_integration_tier(address)
            staking_boost = self.staking_service.calculate_staking_boost(staking_tier)
            staked_amount = self.staking_service.get_staked_amount(address)
            
            # Apply oracle penalty
            oracle_penalty = await self._calculate_oracle_penalty()
            
            # Calculate final score
            final_score = max(0, min(1000, base_score - oracle_penalty + staking_boost))
            
            # Risk band can be improved by staking
            final_risk_band = base_risk_band
            if staking_tier >= 2 and base_risk_band > 1:
                final_risk_band = max(1, base_risk_band - 1)
            
            # Build explanation
            explanation_parts = [base_explanation]
            if model_version_used:
                explanation_parts.append(f"ML model v{model_version_used}")
            if oracle_penalty > 0:
                explanation_parts.append(f"Oracle volatility penalty: -{oracle_penalty} points")
            if staking_boost > 0:
                tier_names = {1: "Bronze", 2: "Silver", 3: "Gold"}
                explanation_parts.append(f"Staking boost ({tier_names.get(staking_tier, 'Unknown')} tier): +{staking_boost} points")
            if staking_tier >= 2 and final_risk_band < base_risk_band:
                explanation_parts.append(f"Risk band improved by staking tier")
            
            explanation = ". ".join(explanation_parts)
            
            duration = time.time() - start_time
            
            # Record metrics
            record_score_computation(
                status="success",
                duration=duration,
                score=final_score
            )
            
            result = {
                "score": final_score,
                "baseScore": base_score,
                "riskBand": final_risk_band,
                "explanation": explanation,
                "stakingBoost": staking_boost,
                "oraclePenalty": oracle_penalty,
                "stakedAmount": staked_amount,
                "stakingTier": staking_tier,
                "features": features,
                "modelVersion": model_version_used,
                "mlUsed": ml_score is not None,
            }
            
            logger.info(
                "Score computation completed",
                extra={
                    "address": address,
                    "score": final_score,
                    "ml_used": ml_score is not None,
                    "model_version": model_version_used,
                }
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            record_score_computation(
                status="error",
                duration=duration
            )
            
            logger.error(
                "Error computing score",
                exc_info=True,
                extra={
                    "address": address,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
            )
            
            return self._default_score_result()
    
    def _score_to_risk_band(self, score: int) -> int:
        """Convert score to risk band"""
        if score >= 750:
            return 1  # Low risk
        elif score >= 500:
            return 2  # Medium risk
        elif score >= 250:
            return 3  # High risk
        else:
            return 3  # High risk
    
    async def _calculate_oracle_penalty(self) -> int:
        """Calculate penalty based on oracle volatility"""
        try:
            volatility = await self.oracle_service.get_volatility('ETH', days=30)
            
            if volatility and volatility > 0.3:
                return 50
            elif volatility and volatility > 0.2:
                return 25
            else:
                return 0
        except Exception as e:
            logger.warning(f"Error calculating oracle penalty: {e}")
            return 0
    
    def _default_score_result(self) -> Dict[str, Any]:
        """Return default score result on error"""
        return {
            "score": 500,
            "baseScore": 500,
            "riskBand": 2,
            "explanation": "Error computing score, using default",
            "stakingBoost": 0,
            "oraclePenalty": 0,
            "stakedAmount": 0,
            "stakingTier": 0,
            "mlUsed": False,
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        if self.model:
            return {
                "version": self.model.model_version,
                "metadata": self.model.get_metadata(),
                "feature_importance": self.model.get_feature_importance(),
            }
        else:
            return {
                "version": None,
                "status": "not_loaded",
            }


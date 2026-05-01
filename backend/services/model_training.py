"""
Model Training Pipeline

Training pipeline for ML models with synthetic data generation,
cross-validation, and model versioning.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.ml_model import MLModel
from data.synthetic_data_generator import SyntheticDataGenerator
from database.models import Score, Transaction
from database.connection import get_db_session
from services.feature_engineering import FeatureEngineering
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelTrainingPipeline:
    """Pipeline for training ML models"""
    
    def __init__(self):
        self.feature_engineering = FeatureEngineering()
        self.synthetic_generator = SyntheticDataGenerator()
    
    async def prepare_training_data(
        self,
        use_real_data: bool = True,
        use_synthetic_data: bool = True,
        synthetic_count: int = 1000,
        real_data_limit: Optional[int] = None
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from real and synthetic sources
        
        Returns:
            Tuple of (features DataFrame, target scores Series)
        """
        all_features = []
        all_scores = []
        
        # Get real data
        if use_real_data:
            real_data = await self._get_real_training_data(limit=real_data_limit)
            all_features.extend([d["features"] for d in real_data])
            all_scores.extend([d["score"] for d in real_data])
            logger.info(f"Loaded {len(real_data)} real training samples")
        
        # Generate synthetic data
        if use_synthetic_data:
            synthetic_data = self.synthetic_generator.generate_features(
                score_range=(0, 1000),
                count=synthetic_count
            )
            
            # Augment if we have real data
            if use_real_data and len(real_data) > 0:
                synthetic_data = self.synthetic_generator.augment_real_data(
                    real_data,
                    augmentation_factor=0.5
                )
            
            all_features.extend([{k: v for k, v in d.items() if k != "target_score"} for d in synthetic_data])
            all_scores.extend([d["target_score"] for d in synthetic_data])
            logger.info(f"Generated {len(synthetic_data)} synthetic training samples")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_features)
        y = pd.Series(all_scores)
        
        # Handle missing values
        df = df.fillna(0)
        
        # Remove target_score if present
        if "target_score" in df.columns:
            df = df.drop(columns=["target_score"])
        
        logger.info(f"Total training data: {len(df)} samples, {len(df.columns)} features")
        
        return df, y
    
    async def _get_real_training_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get real training data from database"""
        try:
            async with get_db_session() as session:
                # Get scores with transactions
                stmt = select(Score).where(Score.score > 0)
                if limit:
                    stmt = stmt.limit(limit)
                
                result = await session.execute(stmt)
                scores = result.scalars().all()
                
                training_data = []
                
                for score in scores:
                    try:
                        # Extract features for this address
                        features = await self.feature_engineering.extract_all_features(score.wallet_address)
                        
                        if features:
                            training_data.append({
                                "wallet_address": score.wallet_address,
                                "features": features,
                                "score": score.score,
                            })
                    except Exception as e:
                        logger.warning(f"Error extracting features for {score.wallet_address}: {e}")
                        continue
                
                return training_data
                
        except Exception as e:
            logger.error(f"Error getting real training data: {e}", exc_info=True)
            return []
    
    async def train_model(
        self,
        hyperparameters: Optional[Dict[str, Any]] = None,
        use_real_data: bool = True,
        use_synthetic_data: bool = True,
        synthetic_count: int = 1000
    ) -> tuple[MLModel, Dict[str, Any]]:
        """
        Train a new ML model
        
        Returns:
            Tuple of (trained model, training metrics)
        """
        try:
            logger.info("Starting model training pipeline")
            
            # Prepare data
            X, y = await self.prepare_training_data(
                use_real_data=use_real_data,
                use_synthetic_data=use_synthetic_data,
                synthetic_count=synthetic_count
            )
            
            if len(X) == 0:
                raise ValueError("No training data available")
            
            # Train model
            model = MLModel()
            metrics = model.train(X, y, hyperparameters=hyperparameters)
            
            # Save model
            model_path = model.save()
            
            logger.info(
                "Model training completed",
                extra={
                    "version": model.model_version,
                    "test_r2": metrics.get("test_r2"),
                    "test_mae": metrics.get("test_mae"),
                }
            )
            
            return model, metrics
            
        except Exception as e:
            logger.error(f"Error in training pipeline: {e}", exc_info=True)
            raise
    
    async def evaluate_model(self, model: MLModel, test_size: float = 0.2) -> Dict[str, Any]:
        """Evaluate model on held-out test set"""
        # This would use a separate test set
        # For now, return model metadata metrics
        return model.get_metadata().get("metrics", {})


"""
ML Model Wrapper

XGBoost model wrapper with versioning, save/load, and explainability.
"""

import os
import pickle
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import xgboost as xgb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import shap

from utils.logger import get_logger

logger = get_logger(__name__)


class MLModel:
    """XGBoost model wrapper with versioning and explainability"""
    
    def __init__(self, model_version: Optional[str] = None):
        self.model_version = model_version or self._generate_version()
        self.model: Optional[xgb.XGBRegressor] = None
        self.feature_names: List[str] = []
        self.model_dir = Path(os.getenv("ML_MODEL_DIR", "backend/models/ml_models"))
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.metadata: Dict[str, Any] = {}
    
    def _generate_version(self) -> str:
        """Generate model version string"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        validation_size: float = 0.1,
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Train XGBoost model
        
        Args:
            X: Feature matrix
            y: Target scores
            test_size: Fraction for test set
            validation_size: Fraction for validation set
            hyperparameters: XGBoost hyperparameters
            
        Returns:
            Training metrics
        """
        try:
            self.feature_names = list(X.columns)
            
            # Default hyperparameters
            default_params = {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42,
                "objective": "reg:squarederror",
            }
            
            if hyperparameters:
                default_params.update(hyperparameters)
            
            # Split data
            X_train, X_temp, y_train, y_temp = train_test_split(
                X, y, test_size=(test_size + validation_size), random_state=42
            )
            
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp, y_temp,
                test_size=test_size / (test_size + validation_size),
                random_state=42
            )
            
            # Train model
            self.model = xgb.XGBRegressor(**default_params)
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=10,
                verbose=False
            )
            
            # Evaluate
            train_pred = self.model.predict(X_train)
            val_pred = self.model.predict(X_val)
            test_pred = self.model.predict(X_test)
            
            train_mae = mean_absolute_error(y_train, train_pred)
            val_mae = mean_absolute_error(y_val, val_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            
            train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
            val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
            test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
            
            train_r2 = r2_score(y_train, train_pred)
            val_r2 = r2_score(y_val, val_pred)
            test_r2 = r2_score(y_test, test_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(
                self.model, X_train, y_train,
                cv=5, scoring="r2", n_jobs=-1
            )
            
            metrics = {
                "train_mae": float(train_mae),
                "val_mae": float(val_mae),
                "test_mae": float(test_mae),
                "train_rmse": float(train_rmse),
                "val_rmse": float(val_rmse),
                "test_rmse": float(test_rmse),
                "train_r2": float(train_r2),
                "val_r2": float(val_r2),
                "test_r2": float(test_r2),
                "cv_mean_r2": float(cv_scores.mean()),
                "cv_std_r2": float(cv_scores.std()),
            }
            
            self.metadata = {
                "version": self.model_version,
                "trained_at": datetime.now().isoformat(),
                "n_features": len(self.feature_names),
                "n_train_samples": len(X_train),
                "n_val_samples": len(X_val),
                "n_test_samples": len(X_test),
                "hyperparameters": default_params,
                "metrics": metrics,
            }
            
            logger.info(
                f"Model trained successfully",
                extra={
                    "version": self.model_version,
                    "test_r2": test_r2,
                    "test_mae": test_mae,
                }
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training model: {e}", exc_info=True)
            raise
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        return self.model.predict(X)
    
    def predict_single(self, features: Dict[str, Any]) -> float:
        """Predict score for a single feature vector"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Convert to DataFrame
        df = pd.DataFrame([features])
        
        # Ensure all features are present
        for feature in self.feature_names:
            if feature not in df.columns:
                df[feature] = 0.0
        
        # Reorder columns
        df = df[self.feature_names]
        
        prediction = self.model.predict(df)[0]
        return float(np.clip(prediction, 0, 1000))  # Clip to valid range
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance.tolist()))
    
    def explain_prediction(self, features: Dict[str, Any], top_n: int = 10) -> Dict[str, Any]:
        """
        Explain a prediction using SHAP values
        
        Args:
            features: Feature dictionary
            top_n: Number of top features to return
            
        Returns:
            Explanation with SHAP values
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([features])
            
            # Ensure all features are present
            for feature in self.feature_names:
                if feature not in df.columns:
                    df[feature] = 0.0
            
            df = df[self.feature_names]
            
            # Calculate SHAP values
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(df)
            
            # Get feature contributions
            contributions = {}
            for i, feature in enumerate(self.feature_names):
                contributions[feature] = float(shap_values[0][i])
            
            # Sort by absolute contribution
            sorted_contributions = sorted(
                contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            prediction = self.model.predict(df)[0]
            
            return {
                "prediction": float(prediction),
                "top_features": [
                    {"feature": feat, "contribution": contrib}
                    for feat, contrib in sorted_contributions[:top_n]
                ],
                "all_contributions": contributions,
            }
            
        except Exception as e:
            logger.warning(f"Error explaining prediction: {e}")
            return {
                "prediction": self.predict_single(features),
                "top_features": [],
                "all_contributions": {},
            }
    
    def save(self, version: Optional[str] = None) -> str:
        """Save model to disk"""
        version = version or self.model_version
        model_path = self.model_dir / f"model_{version}.pkl"
        metadata_path = self.model_dir / f"metadata_{version}.json"
        
        # Save model
        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)
        
        # Save metadata
        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
        
        logger.info(f"Model saved: {model_path}")
        return str(model_path)
    
    def load(self, version: str) -> bool:
        """Load model from disk"""
        try:
            model_path = self.model_dir / f"model_{version}.pkl"
            metadata_path = self.model_dir / f"metadata_{version}.json"
            
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Load model
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            
            # Load metadata
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)
                    self.feature_names = self.metadata.get("feature_names", [])
            
            self.model_version = version
            logger.info(f"Model loaded: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get model metadata"""
        return self.metadata.copy()


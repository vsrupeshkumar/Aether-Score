"""
Unit tests for MLScoringService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.ml_scoring import MLScoringService


@pytest.mark.unit
class TestMLScoringService:
    """Test MLScoringService"""
    
    @pytest.fixture
    def ml_service(self):
        """Create MLScoringService instance with mocked dependencies"""
        with patch('services.ml_scoring.MLModel') as mock_model, \
             patch('services.ml_scoring.FeatureEngineering') as mock_fe, \
             patch('services.ml_scoring.StakingService') as mock_staking, \
             patch('services.ml_scoring.QIEOracleService') as mock_oracle, \
             patch('services.ml_scoring.FeatureStore') as mock_store:
            
            # Mock ML model
            mock_model_instance = Mock()
            mock_model_instance.load.return_value = True
            mock_model_instance.predict_single.return_value = 750
            mock_model_instance.explain_prediction.return_value = {
                "top_features": [
                    {"feature": "transaction_count", "contribution": 0.3},
                    {"feature": "unique_counterparties", "contribution": 0.2},
                ]
            }
            mock_model_instance.model_version = "1.0.0"
            mock_model.return_value = mock_model_instance
            
            # Mock feature engineering
            mock_fe_instance = Mock()
            mock_fe_instance.extract_all_features = AsyncMock(return_value={
                "transaction_count": 100,
                "unique_counterparties": 50,
                "avg_tx_value": 1000.0,
            })
            mock_fe.return_value = mock_fe_instance
            
            # Mock staking service
            mock_staking_instance = Mock()
            mock_staking_instance.get_integration_tier.return_value = 2
            mock_staking_instance.calculate_staking_boost.return_value = 50
            mock_staking_instance.get_staked_amount.return_value = 10000
            mock_staking.return_value = mock_staking_instance
            
            # Mock oracle service
            mock_oracle_instance = Mock()
            mock_oracle_instance.get_price = AsyncMock(return_value=2.5)
            mock_oracle_instance.get_volatility = AsyncMock(return_value=0.25)
            mock_oracle.return_value = mock_oracle_instance
            
            # Mock feature store
            mock_store_instance = Mock()
            mock_store_instance.store_features = AsyncMock()
            mock_store.return_value = mock_store_instance
            
            service = MLScoringService()
            service.model = mock_model_instance
            service.feature_engineering = mock_fe_instance
            service.staking_service = mock_staking_instance
            service.oracle_service = mock_oracle_instance
            service.feature_store = mock_store_instance
            yield service
    
    @pytest.mark.asyncio
    async def test_compute_score_with_ml(self, ml_service):
        """Test score computation with ML model"""
        result = await ml_service.compute_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", use_ml=True)
        
        assert "score" in result
        assert result["score"] >= 0
        assert result["score"] <= 1000
        assert "riskBand" in result
        assert "explanation" in result
        assert "model_version" in result
    
    @pytest.mark.asyncio
    async def test_compute_score_fallback_to_rule_based(self, ml_service):
        """Test fallback to rule-based scoring when ML model unavailable"""
        ml_service.model = None  # No ML model available
        
        with patch('services.ml_scoring.ScoringService') as mock_scoring:
            mock_scoring_instance = Mock()
            mock_scoring_instance.compute_score = AsyncMock(return_value={
                "score": 650,
                "riskBand": 2,
                "explanation": "Rule-based score",
            })
            mock_scoring.return_value = mock_scoring_instance
            
            result = await ml_service.compute_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", use_ml=True)
            
            assert result["score"] == 650
            assert result["riskBand"] == 2
    
    @pytest.mark.asyncio
    async def test_compute_score_no_features(self, ml_service):
        """Test score computation when no features available"""
        ml_service.feature_engineering.extract_all_features = AsyncMock(return_value={})
        
        result = await ml_service.compute_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        
        assert "score" in result
        assert result["score"] >= 0
        assert result["score"] <= 1000
    
    @pytest.mark.asyncio
    async def test_compute_score_ml_prediction_error(self, ml_service):
        """Test handling of ML prediction errors"""
        ml_service.model.predict_single.side_effect = Exception("ML prediction error")
        
        with patch('services.ml_scoring.ScoringService') as mock_scoring:
            mock_scoring_instance = Mock()
            mock_scoring_instance.compute_score = AsyncMock(return_value={
                "score": 600,
                "riskBand": 2,
                "explanation": "Fallback score",
            })
            mock_scoring.return_value = mock_scoring_instance
            
            result = await ml_service.compute_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", use_ml=True)
            
            assert result["score"] == 600  # Should use fallback
    
    @pytest.mark.asyncio
    async def test_compute_score_with_staking_boost(self, ml_service):
        """Test score computation includes staking boost"""
        result = await ml_service.compute_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        
        assert "stakingBoost" in result
        assert result["stakingBoost"] >= 0
        assert "stakedAmount" in result
    
    @pytest.mark.asyncio
    async def test_compute_score_with_oracle_penalty(self, ml_service):
        """Test score computation includes oracle penalty"""
        result = await ml_service.compute_score("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        
        assert "oraclePenalty" in result
        assert result["oraclePenalty"] >= 0


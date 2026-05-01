"""
Unit tests for FraudDetectionService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.fraud_detection import FraudDetectionService


@pytest.mark.unit
class TestFraudDetectionService:
    """Test FraudDetectionService"""
    
    @pytest.fixture
    def fraud_service(self):
        """Create FraudDetectionService instance"""
        with patch('services.fraud_detection.FeatureEngineering') as mock_fe:
            mock_fe_instance = Mock()
            mock_fe_instance.extract_all_features = AsyncMock(return_value={
                "transaction_count": 100,
                "unique_counterparties": 5,
                "avg_tx_value": 1000.0,
                "transaction_regularity": 0.9,
            })
            mock_fe.return_value = mock_fe_instance
            
            service = FraudDetectionService()
            service.feature_engineering = mock_fe_instance
            yield service
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_check_fraud_risk_low_risk(self, fraud_service):
        """Test fraud risk check for low-risk address"""
        with patch('services.fraud_detection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock transaction query
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result
            
            result = await fraud_service.check_fraud_risk("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result["fraud_risk"] < 40
            assert result["risk_level"] in ["low", "medium"]
            assert "address" in result
    
    @pytest.mark.asyncio
    async def test_check_fraud_risk_high_risk(self, fraud_service):
        """Test fraud risk check for high-risk address"""
        # Mock high-risk features
        fraud_service.feature_engineering.extract_all_features = AsyncMock(return_value={
            "transaction_count": 1000,
            "unique_counterparties": 2,  # Very few counterparties (Sybil indicator)
            "avg_tx_value": 1000.0,
            "transaction_regularity": 0.99,  # Very regular (bot-like)
        })
        
        with patch('services.fraud_detection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock transaction query with suspicious pattern
            mock_tx = Mock()
            mock_tx.from_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            mock_tx.to_address = "0x" + "1" * 40
            mock_tx.value = 1000
            
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [mock_tx] * 100
            mock_session.execute.return_value = mock_result
            
            result = await fraud_service.check_fraud_risk("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert "fraud_risk" in result
            assert "risk_level" in result
            assert "indicators" in result
    
    @pytest.mark.asyncio
    async def test_check_fraud_risk_error_handling(self, fraud_service):
        """Test fraud risk check error handling"""
        fraud_service.feature_engineering.extract_all_features = AsyncMock(side_effect=Exception("Database error"))
        
        result = await fraud_service.check_fraud_risk("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        
        assert result["fraud_risk"] == 0
        assert result["risk_level"] == "unknown"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_detect_sybil_low_risk(self, fraud_service):
        """Test Sybil detection for low-risk address"""
        features = {
            "transaction_count": 100,
            "unique_counterparties": 50,  # Many unique counterparties
        }
        
        with patch('services.fraud_detection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result
            
            score = await fraud_service._detect_sybil("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", features)
            
            assert 0 <= score <= 1
            assert score < 0.5  # Low Sybil risk
    
    @pytest.mark.asyncio
    async def test_detect_sybil_high_risk(self, fraud_service):
        """Test Sybil detection for high-risk address"""
        features = {
            "transaction_count": 1000,
            "unique_counterparties": 2,  # Very few counterparties
        }
        
        with patch('services.fraud_detection.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock transactions with few unique addresses
            mock_tx = Mock()
            mock_tx.to_address = "0x" + "1" * 40
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [mock_tx] * 100
            mock_session.execute.return_value = mock_result
            
            score = await fraud_service._detect_sybil("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", features)
            
            assert 0 <= score <= 1
            assert score > 0.5  # High Sybil risk
    
    @pytest.mark.asyncio
    async def test_detect_suspicious_patterns(self, fraud_service):
        """Test suspicious pattern detection"""
        features = {
            "transaction_regularity": 0.99,  # Very regular (suspicious)
            "avg_tx_value": 1000.0,
            "transaction_count": 100,
        }
        
        score = await fraud_service._detect_suspicious_patterns("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", features)
        
        assert 0 <= score <= 1
    
    @pytest.mark.asyncio
    async def test_detect_behavioral_anomalies(self, fraud_service):
        """Test behavioral anomaly detection"""
        features = {
            "transaction_count": 100,
            "avg_tx_value": 1000.0,
            "recent_large_transfers": 5,
        }
        
        score = await fraud_service._detect_behavioral_anomalies("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", features)
        
        assert 0 <= score <= 1


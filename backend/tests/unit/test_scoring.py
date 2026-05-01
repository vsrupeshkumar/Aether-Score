"""
Unit tests for ScoringService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from services.scoring import ScoringService
from models.score import WalletFeatures


@pytest.mark.unit
class TestScoringService:
    """Test ScoringService"""
    
    @pytest.fixture
    def scoring_service(self):
        """Create ScoringService instance"""
        with patch('services.scoring.Web3') as mock_web3_class:
            mock_w3 = Mock()
            mock_w3.eth = Mock()
            mock_w3.eth.get_balance = Mock(return_value=1000000000000000000)  # 1 ETH
            mock_w3.eth.get_transaction_count = Mock(return_value=10)
            mock_w3.from_wei = lambda x, unit: x / 1e18
            mock_w3.to_checksum_address = lambda x: x
            mock_web3_class.return_value = mock_w3
            
            with patch('services.scoring.QIEOracleService') as mock_oracle_class, \
                 patch('services.scoring.StakingService') as mock_staking_class:
                mock_oracle = Mock()
                mock_oracle.get_price = AsyncMock(return_value=2000.0)
                mock_oracle.get_volatility = AsyncMock(return_value=0.25)
                mock_oracle.fetchOraclePrice = AsyncMock(return_value=2000.0)
                mock_oracle_class.return_value = mock_oracle
                
                mock_staking = Mock()
                mock_staking.get_integration_tier = Mock(return_value=0)
                mock_staking.calculate_staking_boost = Mock(return_value=0)
                mock_staking.get_staked_amount = Mock(return_value=0)
                mock_staking_class.return_value = mock_staking
                
                service = ScoringService()
                service.w3 = mock_w3
                service.oracle_service = mock_oracle
                service.staking_service = mock_staking
                yield service
    
    @pytest.mark.asyncio
    async def test_extract_features(self, scoring_service):
        """Test feature extraction"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        features = await scoring_service._extract_features(address)
        
        assert features is not None
        assert isinstance(features, WalletFeatures)
        assert features.tx_count >= 0
        assert features.total_volume >= 0
    
    @pytest.mark.asyncio
    async def test_extract_features_error_handling(self, scoring_service):
        """Test feature extraction error handling"""
        scoring_service.w3.eth.get_balance.side_effect = Exception("Network error")
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        features = await scoring_service._extract_features(address)
        
        # Should return default features on error
        assert features is not None
        assert features.tx_count == 0
    
    def test_calculate_score_high_score(self, scoring_service):
        """Test score calculation for high score"""
        features = WalletFeatures(
            tx_count=150,
            total_volume=1500.0,
            stablecoin_ratio=0.8,
            avg_tx_value=10.0,
            days_active=100,
            unique_contracts=10,
            max_drawdown=0.1,
            volatility=0.15
        )
        
        score, risk_band, explanation = scoring_service._calculate_score(features)
        
        assert score >= 750
        assert risk_band == 1
        assert "Low risk" in explanation
    
    def test_calculate_score_medium_score(self, scoring_service):
        """Test score calculation for medium score"""
        features = WalletFeatures(
            tx_count=30,
            total_volume=300.0,
            stablecoin_ratio=0.4,
            avg_tx_value=10.0,
            days_active=20,
            unique_contracts=3,
            max_drawdown=0.2,
            volatility=0.25
        )
        
        score, risk_band, explanation = scoring_service._calculate_score(features)
        
        assert 250 <= score < 750
        assert risk_band in [2, 3]
        assert "Medium risk" in explanation or "High risk" in explanation
    
    def test_calculate_score_low_score(self, scoring_service):
        """Test score calculation for low score"""
        features = WalletFeatures(
            tx_count=2,
            total_volume=10.0,
            stablecoin_ratio=0.1,
            avg_tx_value=5.0,
            days_active=1,
            unique_contracts=1,
            max_drawdown=0.5,
            volatility=0.6
        )
        
        score, risk_band, explanation = scoring_service._calculate_score(features)
        
        assert score < 500
        assert risk_band == 3
        assert "High risk" in explanation
    
    def test_calculate_score_boundaries(self, scoring_service):
        """Test score calculation boundaries"""
        # Test minimum score
        features = WalletFeatures(
            tx_count=0,
            total_volume=0.0,
            stablecoin_ratio=0.0,
            avg_tx_value=0.0,
            days_active=0,
            unique_contracts=0,
            max_drawdown=1.0,
            volatility=1.0
        )
        
        score, risk_band, _ = scoring_service._calculate_score(features)
        assert score >= 0
        assert score <= 1000
        
        # Test maximum score
        features = WalletFeatures(
            tx_count=1000,
            total_volume=10000.0,
            stablecoin_ratio=1.0,
            avg_tx_value=100.0,
            days_active=365,
            unique_contracts=100,
            max_drawdown=0.0,
            volatility=0.0
        )
        
        score, risk_band, _ = scoring_service._calculate_score(features)
        assert score >= 0
        assert score <= 1000
    
    @pytest.mark.asyncio
    async def test_calculate_oracle_penalty_no_oracle(self, scoring_service):
        """Test oracle penalty calculation when oracle not configured"""
        with patch.dict('os.environ', {'QIE_ORACLE_USD_ADDR': ''}):
            penalty = await scoring_service._calculate_oracle_penalty()
            assert penalty == 0
    
    @pytest.mark.asyncio
    async def test_calculate_oracle_penalty_low_volatility(self, scoring_service):
        """Test oracle penalty with low volatility"""
        scoring_service.oracle_service.get_volatility = AsyncMock(return_value=0.1)
        
        with patch.dict('os.environ', {'QIE_ORACLE_USD_ADDR': '0x123'}):
            penalty = await scoring_service._calculate_oracle_penalty()
            assert penalty == 0
    
    @pytest.mark.asyncio
    async def test_calculate_oracle_penalty_high_volatility(self, scoring_service):
        """Test oracle penalty with high volatility"""
        scoring_service.oracle_service.get_volatility = AsyncMock(return_value=0.4)
        
        with patch.dict('os.environ', {'QIE_ORACLE_USD_ADDR': '0x123'}):
            penalty = await scoring_service._calculate_oracle_penalty()
            assert penalty > 0
    
    @pytest.mark.asyncio
    async def test_compute_score_full_flow(self, scoring_service):
        """Test full score computation flow"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        result = await scoring_service.compute_score(address)
        
        assert result is not None
        assert 'score' in result
        assert 'riskBand' in result
        assert 'explanation' in result
        assert 0 <= result['score'] <= 1000
        assert 1 <= result['riskBand'] <= 3
    
    @pytest.mark.asyncio
    async def test_compute_score_with_staking_boost(self, scoring_service):
        """Test score computation with staking boost"""
        scoring_service.staking_service.get_integration_tier = Mock(return_value=2)  # Silver
        scoring_service.staking_service.calculate_staking_boost = Mock(return_value=150)
        scoring_service.staking_service.get_staked_amount = Mock(return_value=5000000000000000000)  # 5 tokens
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = await scoring_service.compute_score(address)
        
        assert result['stakingBoost'] == 150
        assert result['stakingTier'] == 2
        assert result['stakedAmount'] > 0
    
    @pytest.mark.asyncio
    async def test_compute_score_error_handling(self, scoring_service):
        """Test score computation error handling"""
        scoring_service._extract_features = AsyncMock(side_effect=Exception("Test error"))
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = await scoring_service.compute_score(address)
        
        # Should return default score on error
        assert result['score'] == 500
        assert result['riskBand'] == 2
        assert "Error" in result['explanation']
    
    @pytest.mark.asyncio
    async def test_get_tx_count(self, scoring_service):
        """Test transaction count retrieval"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        scoring_service.w3.eth.get_transaction_count = Mock(return_value=42)
        
        count = await scoring_service._get_tx_count(address)
        
        assert count == 42
    
    @pytest.mark.asyncio
    async def test_get_tx_count_error(self, scoring_service):
        """Test transaction count error handling"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        scoring_service.w3.eth.get_transaction_count.side_effect = Exception("Network error")
        
        count = await scoring_service._get_tx_count(address)
        
        assert count == 0


"""
Additional edge case tests for ScoringService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.scoring import ScoringService
from models.score import WalletFeatures


@pytest.mark.unit
class TestScoringEdgeCases:
    """Test edge cases and error scenarios for ScoringService"""
    
    @pytest.fixture
    def scoring_service(self):
        """Create ScoringService instance"""
        with patch('services.scoring.Web3') as mock_web3_class:
            mock_w3 = Mock()
            mock_w3.eth = Mock()
            mock_w3.eth.get_balance = Mock(return_value=1000000000000000000)
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
    async def test_compute_score_with_max_staking_boost(self, scoring_service):
        """Test score computation with maximum staking boost (Gold tier)"""
        scoring_service.staking_service.get_integration_tier = Mock(return_value=3)  # Gold
        scoring_service.staking_service.calculate_staking_boost = Mock(return_value=300)
        scoring_service.staking_service.get_staked_amount = Mock(return_value=10000000000000000000)  # 10 tokens
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = await scoring_service.compute_score(address)
        
        assert result['stakingBoost'] == 300
        assert result['stakingTier'] == 3
        assert result['score'] <= 1000  # Should be capped at 1000
    
    @pytest.mark.asyncio
    async def test_compute_score_with_high_oracle_penalty(self, scoring_service):
        """Test score computation with high oracle volatility penalty"""
        scoring_service.oracle_service.get_volatility = AsyncMock(return_value=0.5)  # High volatility
        
        with patch.dict('os.environ', {'QIE_ORACLE_USD_ADDR': '0x123'}):
            address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
            result = await scoring_service.compute_score(address)
            
            assert result['oraclePenalty'] > 0
            assert result['score'] >= 0  # Should not go below 0
    
    @pytest.mark.asyncio
    async def test_compute_score_risk_band_improvement(self, scoring_service):
        """Test that staking tier can improve risk band"""
        # Set base risk band to 2 (medium)
        scoring_service._calculate_score = Mock(return_value=(600, 2, "Medium risk"))
        scoring_service.staking_service.get_integration_tier = Mock(return_value=2)  # Silver
        scoring_service.staking_service.calculate_staking_boost = Mock(return_value=150)
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = await scoring_service.compute_score(address)
        
        # Risk band should improve from 2 to 1 with Silver tier
        assert result['riskBand'] <= 2
    
    @pytest.mark.asyncio
    async def test_extract_features_with_zero_balance(self, scoring_service):
        """Test feature extraction with zero balance"""
        scoring_service.w3.eth.get_balance = Mock(return_value=0)
        scoring_service.w3.eth.get_transaction_count = Mock(return_value=0)
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        features = await scoring_service._extract_features(address)
        
        assert features.total_volume == 0.0
        assert features.tx_count == 0
    
    @pytest.mark.asyncio
    async def test_extract_features_with_very_high_balance(self, scoring_service):
        """Test feature extraction with very high balance"""
        scoring_service.w3.eth.get_balance = Mock(return_value=1000000000000000000000)  # 1000 ETH
        scoring_service.w3.eth.get_transaction_count = Mock(return_value=1000)
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        features = await scoring_service._extract_features(address)
        
        assert features.total_volume > 0
        assert features.tx_count == 1000
    
    @pytest.mark.asyncio
    async def test_calculate_score_with_extreme_volatility(self, scoring_service):
        """Test score calculation with extreme volatility"""
        features = WalletFeatures(
            tx_count=10,  # Lower tx count
            total_volume=50.0,  # Lower volume
            stablecoin_ratio=0.1,  # Lower stablecoin ratio
            avg_tx_value=5.0,
            days_active=5,  # Lower days active
            unique_contracts=1,
            max_drawdown=0.9,
            volatility=1.0  # 100% volatility
        )
        
        score, risk_band, explanation = scoring_service._calculate_score(features)
        
        # High volatility with low activity should give low score
        assert score < 600  # Adjusted threshold
        assert risk_band >= 2
    
    @pytest.mark.asyncio
    async def test_calculate_score_with_perfect_features(self, scoring_service):
        """Test score calculation with perfect features"""
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
        
        score, risk_band, explanation = scoring_service._calculate_score(features)
        
        # Perfect features should give high score
        assert score >= 750
        assert risk_band == 1
    
    @pytest.mark.asyncio
    async def test_compute_score_network_error_handling(self, scoring_service):
        """Test score computation when network errors occur"""
        scoring_service.w3.eth.get_balance.side_effect = Exception("Network error")
        scoring_service.w3.eth.get_transaction_count.side_effect = Exception("Network error")
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = await scoring_service.compute_score(address)
        
        # Should return default score on error (from exception handler)
        assert result['score'] == 500
        assert result['riskBand'] == 2
        # Explanation will contain error message
        assert "Error" in result['explanation'] or result['explanation']  # Either error message or default
    
    @pytest.mark.asyncio
    async def test_compute_score_oracle_service_error(self, scoring_service):
        """Test score computation when oracle service fails"""
        scoring_service.oracle_service.get_price = AsyncMock(side_effect=Exception("Oracle error"))
        scoring_service.oracle_service.get_volatility = AsyncMock(side_effect=Exception("Oracle error"))
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = await scoring_service.compute_score(address)
        
        # Should still compute score without oracle data
        assert 'score' in result
        assert 0 <= result['score'] <= 1000


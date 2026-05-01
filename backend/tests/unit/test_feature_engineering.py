"""
Unit tests for FeatureEngineering service
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from services.feature_engineering import FeatureEngineering
from database.models import Transaction, TokenTransfer


@pytest.mark.unit
class TestFeatureEngineering:
    """Test FeatureEngineering service"""
    
    @pytest.fixture
    def feature_service(self):
        """Create FeatureEngineering instance"""
        return FeatureEngineering()
    
    @pytest.fixture
    def mock_transactions(self):
        """Create mock transactions"""
        transactions = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(10):
            tx = Mock(spec=Transaction)
            tx.tx_hash = f"0x{'a' * 64}"
            tx.block_timestamp = base_time + timedelta(days=i)
            tx.value = 1000.0 * (i + 1)
            tx.from_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            tx.to_address = f"0x{'1' * 40}" if i % 2 == 0 else f"0x{'2' * 40}"
            tx.gas_used = 21000 + i * 1000
            tx.gas_price = 1000000000
            tx.status = "success"
            transactions.append(tx)
        
        return transactions
    
    @pytest.fixture
    def mock_token_transfers(self):
        """Create mock token transfers"""
        transfers = []
        for i in range(5):
            transfer = Mock(spec=TokenTransfer)
            transfer.token_address = f"0x{'3' * 40}"
            transfer.token_type = "ERC20"
            transfer.amount = 1000 * (i + 1)
            transfer.from_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            transfer.to_address = f"0x{'4' * 40}"
            transfers.append(transfer)
        
        return transfers
    
    @pytest.mark.asyncio
    async def test_extract_all_features(self, feature_service, mock_transactions, mock_token_transfers):
        """Test extracting all features"""
        with patch.object(feature_service, '_get_transactions', new_callable=AsyncMock) as mock_get_tx, \
             patch.object(feature_service, '_get_token_transfers', new_callable=AsyncMock) as mock_get_tt, \
             patch.object(feature_service, '_extract_transaction_patterns', new_callable=AsyncMock) as mock_tx_patterns, \
             patch.object(feature_service, '_extract_token_holdings', new_callable=AsyncMock) as mock_token_holdings, \
             patch.object(feature_service, '_extract_defi_interactions', new_callable=AsyncMock) as mock_defi, \
             patch.object(feature_service, '_extract_network_features', new_callable=AsyncMock) as mock_network, \
             patch.object(feature_service, '_extract_temporal_features', new_callable=AsyncMock) as mock_temporal, \
             patch.object(feature_service, '_extract_financial_metrics', new_callable=AsyncMock) as mock_financial, \
             patch.object(feature_service, '_extract_behavioral_features', new_callable=AsyncMock) as mock_behavioral, \
             patch('services.feature_engineering.get_db_session') as mock_session:
            
            mock_session.return_value.__aenter__.return_value = Mock()
            mock_get_tx.return_value = mock_transactions
            mock_get_tt.return_value = mock_token_transfers
            mock_tx_patterns.return_value = {"transaction_count": 10}
            mock_token_holdings.return_value = {"token_diversity": 5}
            mock_defi.return_value = {"defi_interactions": 2}
            mock_network.return_value = {"unique_addresses": 3}
            mock_temporal.return_value = {"account_age_days": 30}
            mock_financial.return_value = {"total_value": 10000}
            mock_behavioral.return_value = {"avg_gas_price": 1000000000}
            
            features = await feature_service.extract_all_features("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert isinstance(features, dict)
            assert "transaction_count" in features
            assert "token_diversity" in features
    
    @pytest.mark.asyncio
    async def test_extract_all_features_error_handling(self, feature_service):
        """Test error handling in feature extraction"""
        with patch('services.feature_engineering.get_db_session', side_effect=Exception("Database error")):
            features = await feature_service.extract_all_features("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert features == {}
    
    @pytest.mark.asyncio
    async def test_extract_transaction_patterns(self, feature_service, mock_transactions):
        """Test transaction pattern extraction"""
        patterns = await feature_service._extract_transaction_patterns(mock_transactions)
        
        assert isinstance(patterns, dict)
        assert "transaction_count" in patterns or "tx_frequency" in patterns
    
    @pytest.mark.asyncio
    async def test_extract_token_holdings(self, feature_service, mock_token_transfers):
        """Test token holdings extraction"""
        holdings = await feature_service._extract_token_holdings(mock_token_transfers)
        
        assert isinstance(holdings, dict)
    
    @pytest.mark.asyncio
    async def test_extract_defi_interactions(self, feature_service, mock_transactions):
        """Test DeFi interaction extraction"""
        defi = await feature_service._extract_defi_interactions(mock_transactions)
        
        assert isinstance(defi, dict)
    
    @pytest.mark.asyncio
    async def test_extract_network_features(self, feature_service, mock_transactions, mock_token_transfers):
        """Test network feature extraction"""
        network = await feature_service._extract_network_features(mock_transactions, mock_token_transfers)
        
        assert isinstance(network, dict)
    
    @pytest.mark.asyncio
    async def test_extract_temporal_features(self, feature_service, mock_transactions):
        """Test temporal feature extraction"""
        temporal = await feature_service._extract_temporal_features(mock_transactions)
        
        assert isinstance(temporal, dict)
        # Should include account age or similar
        assert any("age" in key.lower() or "time" in key.lower() for key in temporal.keys())
    
    @pytest.mark.asyncio
    async def test_extract_financial_metrics(self, feature_service, mock_transactions, mock_token_transfers):
        """Test financial metrics extraction"""
        financial = await feature_service._extract_financial_metrics(mock_transactions, mock_token_transfers)
        
        assert isinstance(financial, dict)
    
    @pytest.mark.asyncio
    async def test_extract_behavioral_features(self, feature_service, mock_transactions):
        """Test behavioral feature extraction"""
        behavioral = await feature_service._extract_behavioral_features(mock_transactions)
        
        assert isinstance(behavioral, dict)


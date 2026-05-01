"""
Unit tests for GDPRService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.gdpr import GDPRService


@pytest.mark.unit
class TestGDPRService:
    """Test GDPRService"""
    
    @pytest.fixture
    def gdpr_service(self):
        """Create GDPRService instance"""
        return GDPRService()
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_delete_user_data(self, gdpr_service, mock_session):
        """Test deleting user data"""
        with patch('services.gdpr.UserRepository') as mock_user_repo, \
             patch('services.gdpr.ScoreRepository') as mock_score_repo, \
             patch('services.gdpr.TransactionRepository') as mock_tx_repo:
            
            mock_user_repo.delete_user = AsyncMock()
            mock_score_repo.delete_score = AsyncMock()
            mock_tx_repo.delete_user_transactions = AsyncMock()
            
            result = await gdpr_service.delete_user_data(mock_session, "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result["success"] is True
            mock_user_repo.delete_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_user_data(self, gdpr_service, mock_session):
        """Test exporting user data"""
        with patch('services.gdpr.UserRepository') as mock_user_repo, \
             patch('services.gdpr.ScoreRepository') as mock_score_repo, \
             patch('services.gdpr.TransactionRepository') as mock_tx_repo:
            
            # Mock user data
            mock_user = Mock()
            mock_user.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            mock_user.email = "test@example.com"
            mock_user_repo.get_user = AsyncMock(return_value=mock_user)
            
            mock_score = Mock()
            mock_score.score = 750
            mock_score.risk_band = 1
            mock_score_repo.get_score = AsyncMock(return_value=mock_score)
            
            mock_tx_repo.get_transactions_by_user = AsyncMock(return_value=[])
            
            result = await gdpr_service.export_user_data(mock_session, "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert "wallet_address" in result
            assert "scores" in result
            assert "transactions" in result
    
    @pytest.mark.asyncio
    async def test_delete_user_data_not_found(self, gdpr_service, mock_session):
        """Test deleting non-existent user data"""
        with patch('services.gdpr.UserRepository') as mock_user_repo:
            mock_user_repo.get_user = AsyncMock(return_value=None)
            
            result = await gdpr_service.delete_user_data(mock_session, "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result["success"] is False
            assert "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_export_user_data_not_found(self, gdpr_service, mock_session):
        """Test exporting non-existent user data"""
        with patch('services.gdpr.UserRepository') as mock_user_repo:
            mock_user_repo.get_user = AsyncMock(return_value=None)
            
            result = await gdpr_service.export_user_data(mock_session, "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result is None


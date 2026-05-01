"""
Unit tests for LoanLiquidationService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from services.loan_liquidation import LoanLiquidationService
from database.models import Loan


@pytest.mark.unit
class TestLoanLiquidationService:
    """Test LoanLiquidationService"""
    
    @pytest.fixture
    def liquidation_service(self):
        """Create LoanLiquidationService instance"""
        with patch('services.loan_liquidation.BlockchainService') as mock_blockchain, \
             patch('services.loan_liquidation.MLScoringService') as mock_scoring:
            
            mock_blockchain_instance = Mock()
            mock_blockchain_instance.update_score = AsyncMock(return_value="0x" + "a" * 64)
            mock_blockchain.return_value = mock_blockchain_instance
            
            mock_scoring_instance = Mock()
            mock_scoring_instance.compute_score = AsyncMock(return_value={"score": 500})
            mock_scoring_instance._determine_risk_band = Mock(return_value=2)
            mock_scoring.return_value = mock_scoring_instance
            
            service = LoanLiquidationService()
            service.blockchain_service = mock_blockchain_instance
            service.scoring_service = mock_scoring_instance
            yield service
    
    @pytest.fixture
    def mock_loan_defaulted(self):
        """Create mock defaulted loan"""
        loan = Mock(spec=Loan)
        loan.id = 1
        loan.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        loan.amount = 1000
        loan.status = "defaulted"
        loan.collateral_amount = 1500
        loan.collateral_token = "0x" + "1" * 40
        loan.defaulted_at = datetime.now()
        return loan
    
    @pytest.fixture
    def mock_loan_active(self):
        """Create mock active loan"""
        loan = Mock(spec=Loan)
        loan.id = 2
        loan.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        loan.amount = 1000
        loan.status = "active"
        return loan
    
    @pytest.mark.asyncio
    async def test_liquidate_loan_success(self, liquidation_service, mock_loan_defaulted):
        """Test successful loan liquidation"""
        with patch('services.loan_liquidation.get_db_session') as mock_session:
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            mock_session_obj.get = AsyncMock(return_value=mock_loan_defaulted)
            
            result = await liquidation_service.liquidate_loan(1)
            
            assert result["status"] == "success"
            assert result["loan_id"] == 1
            assert "liquidation_amount" in result
    
    @pytest.mark.asyncio
    async def test_liquidate_loan_not_defaulted(self, liquidation_service, mock_loan_active):
        """Test liquidating non-defaulted loan"""
        with patch('services.loan_liquidation.get_db_session') as mock_session:
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            mock_session_obj.get = AsyncMock(return_value=mock_loan_active)
            
            result = await liquidation_service.liquidate_loan(2)
            
            assert result["status"] == "error"
            assert "not in default" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_liquidate_loan_not_found(self, liquidation_service):
        """Test liquidating non-existent loan"""
        with patch('services.loan_liquidation.get_db_session') as mock_session:
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            mock_session_obj.get = AsyncMock(return_value=None)
            
            result = await liquidation_service.liquidate_loan(999)
            
            assert result["status"] == "error"
            assert "not found" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_liquidate_loan_already_liquidated(self, liquidation_service):
        """Test liquidating already liquidated loan"""
        loan = Mock(spec=Loan)
        loan.id = 3
        loan.status = "liquidated"
        
        with patch('services.loan_liquidation.get_db_session') as mock_session:
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            mock_session_obj.get = AsyncMock(return_value=loan)
            
            result = await liquidation_service.liquidate_loan(3)
            
            assert result["status"] == "error"
            assert "already liquidated" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_batch_liquidate(self, liquidation_service, mock_loan_defaulted):
        """Test batch liquidation"""
        with patch.object(liquidation_service, 'liquidate_loan', new_callable=AsyncMock) as mock_liquidate:
            mock_liquidate.return_value = {"status": "success", "loan_id": 1}
            
            result = await liquidation_service.batch_liquidate([1, 2, 3])
            
            assert "successful" in result
            assert "failed" in result
            assert len(result["successful"]) == 3


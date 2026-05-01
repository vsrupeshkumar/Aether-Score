"""
Unit tests for RiskModelingService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.risk_models import RiskModelingService
from database.models import Loan


@pytest.mark.unit
class TestRiskModelingService:
    """Test RiskModelingService"""
    
    @pytest.fixture
    def risk_service(self):
        """Create RiskModelingService instance"""
        with patch('services.risk_models.MLScoringService') as mock_scoring, \
             patch('services.risk_models.QIEOracleService') as mock_oracle:
            
            mock_scoring_instance = Mock()
            mock_scoring_instance.compute_score = AsyncMock(return_value={"score": 750})
            mock_scoring.return_value = mock_scoring_instance
            
            mock_oracle_instance = Mock()
            mock_oracle_instance.get_price = AsyncMock(return_value=2.5)
            mock_oracle_instance.get_volatility = AsyncMock(return_value=0.25)
            mock_oracle.return_value = mock_oracle_instance
            
            service = RiskModelingService()
            service.ml_scoring_service = mock_scoring_instance
            service.oracle_service = mock_oracle_instance
            yield service
    
    @pytest.fixture
    def mock_loan(self):
        """Create mock loan"""
        loan = Mock(spec=Loan)
        loan.id = 1
        loan.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        loan.amount = 1000
        loan.collateral_amount = 1500
        loan.collateral_token = "0x" + "1" * 40
        return loan
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_calculate_loan_risk(self, risk_service, mock_session, mock_loan):
        """Test calculating risk for a single loan"""
        with patch('services.risk_models.LoanRepository') as mock_repo:
            mock_repo.get_loan_by_id = AsyncMock(return_value=mock_loan)
            
            result = await risk_service.calculate_loan_risk(mock_session, 1)
            
            assert result["status"] == "success"
            assert "probability_of_default" in result
            assert "loss_given_default" in result
            assert "exposure_at_default" in result
            assert "expected_loss" in result
            assert 0 <= result["probability_of_default"] <= 1
            assert 0 <= result["loss_given_default"] <= 1
    
    @pytest.mark.asyncio
    async def test_calculate_loan_risk_no_collateral(self, risk_service, mock_session):
        """Test calculating risk for loan without collateral"""
        loan = Mock(spec=Loan)
        loan.id = 2
        loan.amount = 1000
        loan.collateral_amount = None
        loan.collateral_token = None
        
        with patch('services.risk_models.LoanRepository') as mock_repo:
            mock_repo.get_loan_by_id = AsyncMock(return_value=loan)
            
            result = await risk_service.calculate_loan_risk(mock_session, 2)
            
            assert result["loss_given_default"] == 1.0  # 100% loss if no collateral
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_risk(self, risk_service, mock_session):
        """Test calculating portfolio risk"""
        mock_loan1 = Mock(spec=Loan)
        mock_loan1.id = 1
        mock_loan1.status = "active"
        mock_loan2 = Mock(spec=Loan)
        mock_loan2.id = 2
        mock_loan2.status = "defaulted"
        
        with patch('services.risk_models.LoanRepository') as mock_repo, \
             patch.object(risk_service, 'calculate_loan_risk', new_callable=AsyncMock) as mock_loan_risk:
            
            mock_repo.get_loans_by_user = AsyncMock(return_value=[mock_loan1, mock_loan2])
            mock_loan_risk.return_value = {
                "status": "success",
                "expected_loss": 100.0,
                "exposure_at_default": 1000.0,
            }
            
            result = await risk_service.calculate_portfolio_risk(mock_session)
            
            assert result["status"] == "success"
            assert "portfolio_size" in result
            assert "total_exposure" in result
            assert "total_expected_loss" in result
            assert "default_rate" in result
    
    @pytest.mark.asyncio
    async def test_calculate_market_risk(self, risk_service, mock_session):
        """Test calculating market risk"""
        result = await risk_service.calculate_market_risk(mock_session, "QIE")
        
        assert result["status"] == "success"
        assert "volatility_30d" in result
        assert "current_price_usd" in result
    
    @pytest.mark.asyncio
    async def test_calculate_liquidity_risk(self, risk_service, mock_session):
        """Test calculating liquidity risk"""
        result = await risk_service.calculate_liquidity_risk(mock_session, "QIE")
        
        assert result["status"] == "success"
        assert "liquidity_score" in result
        assert 0 <= result["liquidity_score"] <= 1


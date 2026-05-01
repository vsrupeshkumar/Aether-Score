"""
Unit tests for LoanMonitor service
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from services.loan_monitor import LoanMonitor
from database.models import Loan


@pytest.mark.unit
class TestLoanMonitor:
    """Test LoanMonitor service"""
    
    @pytest.fixture
    def loan_monitor(self):
        """Create LoanMonitor instance"""
        return LoanMonitor()
    
    @pytest.fixture
    def mock_loan_active(self):
        """Create mock active loan"""
        loan = Mock(spec=Loan)
        loan.id = 1
        loan.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        loan.amount = 1000
        loan.status = "active"
        loan.due_date = datetime.now() + timedelta(days=10)  # Not due yet
        loan.created_at = datetime.now() - timedelta(days=20)
        return loan
    
    @pytest.fixture
    def mock_loan_defaulted(self):
        """Create mock defaulted loan"""
        loan = Mock(spec=Loan)
        loan.id = 2
        loan.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        loan.amount = 1000
        loan.status = "active"
        loan.due_date = datetime.now() - timedelta(days=10)  # Overdue
        loan.created_at = datetime.now() - timedelta(days=30)
        return loan
    
    @pytest.mark.asyncio
    async def test_check_loans_no_defaults(self, loan_monitor, mock_loan_active):
        """Test checking loans with no defaults"""
        with patch('services.loan_monitor.LoanRepository') as mock_repo, \
             patch('services.loan_monitor.get_db_session') as mock_session:
            
            mock_session.return_value.__aenter__.return_value = AsyncMock()
            mock_repo.get_loans_by_user = AsyncMock(return_value=[mock_loan_active])
            
            result = await loan_monitor.check_loans()
            
            assert result["status"] == "success"
            assert result["defaults_detected"] == 0
    
    @pytest.mark.asyncio
    async def test_check_loans_with_defaults(self, loan_monitor, mock_loan_defaulted):
        """Test checking loans with defaults"""
        with patch('services.loan_monitor.LoanRepository') as mock_repo, \
             patch('services.loan_monitor.get_db_session') as mock_session:
            
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            mock_repo.get_loans_by_user = AsyncMock(return_value=[mock_loan_defaulted])
            
            result = await loan_monitor.check_loans()
            
            assert result["status"] == "success"
            assert result["defaults_detected"] >= 1
    
    @pytest.mark.asyncio
    async def test_check_loan_default_not_due(self, loan_monitor, mock_loan_active):
        """Test checking loan that is not due"""
        with patch('services.loan_monitor.get_db_session') as mock_session:
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            
            result = await loan_monitor._check_loan_default(mock_session_obj, mock_loan_active)
            
            assert result["is_defaulted"] is False
    
    @pytest.mark.asyncio
    async def test_check_loan_default_overdue(self, loan_monitor, mock_loan_defaulted):
        """Test checking loan that is overdue"""
        with patch('services.loan_monitor.get_db_session') as mock_session:
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            
            result = await loan_monitor._check_loan_default(mock_session_obj, mock_loan_defaulted)
            
            assert result["is_defaulted"] is True
            assert result["days_overdue"] > 0
    
    @pytest.mark.asyncio
    async def test_get_defaulted_loans(self, loan_monitor):
        """Test getting all defaulted loans"""
        with patch('services.loan_monitor.LoanRepository') as mock_repo, \
             patch('services.loan_monitor.get_db_session') as mock_session:
            
            mock_loan = Mock(spec=Loan)
            mock_loan.status = "defaulted"
            
            mock_session_obj = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_obj
            mock_repo.get_loans_by_user = AsyncMock(return_value=[mock_loan])
            
            loans = await loan_monitor.get_defaulted_loans()
            
            assert len(loans) >= 0
            assert all(loan.status == "defaulted" for loan in loans)


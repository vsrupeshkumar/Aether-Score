"""
Integration tests for /api/oracle/price endpoint
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient
from app import app


@pytest.mark.integration
class TestAPIOracle:
    """Test /api/oracle/price endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_get_oracle_price_success(self, client):
        """Test successful oracle price retrieval"""
        with patch('app.QIEOracleService') as mock_oracle:
            mock_oracle_instance = Mock()
            mock_oracle_instance.fetchOraclePrice = AsyncMock(return_value=2.5)
            mock_oracle.return_value = mock_oracle_instance
            
            response = client.get("/api/oracle/price")
            
            assert response.status_code == 200
            data = response.json()
            assert "price" in data
            assert data["price"] == 2.5
            assert "timestamp" in data
    
    def test_get_oracle_price_not_configured(self, client):
        """Test oracle price when oracle address not configured"""
        with patch.dict('os.environ', {'QIE_ORACLE_USD_ADDR': '0x0000000000000000000000000000000000000000'}):
            response = client.get("/api/oracle/price")
            
            assert response.status_code == 200
            data = response.json()
            assert data["price"] is None
            assert "error" in data
    
    def test_get_oracle_price_error(self, client):
        """Test oracle price error handling"""
        with patch('app.QIEOracleService') as mock_oracle:
            mock_oracle_instance = Mock()
            mock_oracle_instance.fetchOraclePrice = AsyncMock(side_effect=Exception("Oracle error"))
            mock_oracle.return_value = mock_oracle_instance
            
            response = client.get("/api/oracle/price")
            
            assert response.status_code == 500


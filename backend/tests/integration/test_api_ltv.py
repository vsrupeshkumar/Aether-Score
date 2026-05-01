"""
Integration tests for /api/lending/ltv/{address} endpoint
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient
from app import app


@pytest.mark.integration
class TestAPILTV:
    """Test /api/lending/ltv/{address} endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_get_ltv_success(self, client):
        """Test successful LTV retrieval"""
        with patch('app.scoring_service') as mock_scoring:
            mock_scoring.compute_score = AsyncMock(return_value={
                "score": 750,
                "riskBand": 1,
            })
            
            response = client.get("/api/lending/ltv/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert response.status_code == 200
            data = response.json()
            assert "ltvBps" in data
            assert "ltvPercent" in data
            assert "riskBand" in data
            assert "score" in data
            # Risk band 1 should have 70% LTV (7000 bps)
            assert data["ltvBps"] == 7000
            assert data["ltvPercent"] == 70.0
    
    def test_get_ltv_risk_band_2(self, client):
        """Test LTV for risk band 2"""
        with patch('app.scoring_service') as mock_scoring:
            mock_scoring.compute_score = AsyncMock(return_value={
                "score": 550,
                "riskBand": 2,
            })
            
            response = client.get("/api/lending/ltv/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert response.status_code == 200
            data = response.json()
            # Risk band 2 should have 50% LTV (5000 bps)
            assert data["ltvBps"] == 5000
            assert data["ltvPercent"] == 50.0
    
    def test_get_ltv_risk_band_3(self, client):
        """Test LTV for risk band 3"""
        with patch('app.scoring_service') as mock_scoring:
            mock_scoring.compute_score = AsyncMock(return_value={
                "score": 350,
                "riskBand": 3,
            })
            
            response = client.get("/api/lending/ltv/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert response.status_code == 200
            data = response.json()
            # Risk band 3 should have 30% LTV (3000 bps)
            assert data["ltvBps"] == 3000
            assert data["ltvPercent"] == 30.0
    
    def test_get_ltv_invalid_address(self, client):
        """Test LTV with invalid address"""
        response = client.get("/api/lending/ltv/invalid_address")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_ltv_error(self, client):
        """Test LTV error handling"""
        with patch('app.scoring_service') as mock_scoring:
            mock_scoring.compute_score = AsyncMock(side_effect=Exception("Scoring error"))
            
            response = client.get("/api/lending/ltv/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert response.status_code == 500


"""
Integration tests for /api/update-on-chain endpoint
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app import app


@pytest.mark.integration
class TestAPIUpdateOnChain:
    """Test /api/update-on-chain endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_update_on_chain_success(self, client):
        """Test successful on-chain update"""
        with patch('middleware.auth.get_current_user', return_value="test_user"), \
             patch('app.blockchain_service') as mock_blockchain:
            
            mock_blockchain.update_score = AsyncMock(return_value="0x" + "a" * 64)
            
            response = client.post(
                "/api/update-on-chain",
                json={
                    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "score": 750,
                    "riskBand": 1
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "transactionHash" in data
            assert data["transactionHash"] == "0x" + "a" * 64
    
    def test_update_on_chain_no_auth(self, client):
        """Test update on-chain without authentication"""
        response = client.post(
            "/api/update-on-chain",
            json={
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "score": 750,
                "riskBand": 1
            }
        )
        
        assert response.status_code == 401
    
    def test_update_on_chain_invalid_address(self, client):
        """Test update on-chain with invalid address"""
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            response = client.post(
                "/api/update-on-chain",
                json={
                    "address": "invalid_address",
                    "score": 750,
                    "riskBand": 1
                }
            )
            
            assert response.status_code == 422  # Validation error
    
    def test_update_on_chain_blockchain_error(self, client):
        """Test update on-chain when blockchain update fails"""
        with patch('middleware.auth.get_current_user', return_value="test_user"), \
             patch('app.blockchain_service') as mock_blockchain:
            
            mock_blockchain.update_score = AsyncMock(side_effect=Exception("Blockchain error"))
            
            response = client.post(
                "/api/update-on-chain",
                json={
                    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "score": 750,
                    "riskBand": 1
                }
            )
            
            assert response.status_code == 500


"""
Integration tests for /api/score endpoint
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from httpx import AsyncClient
from app import app


@pytest.mark.integration
class TestAPIScore:
    """Test /api/score endpoint"""
    
    @pytest.fixture
    async def client(self):
        """Create async test client"""
        from httpx import AsyncClient
        from fastapi.testclient import TestClient
        # Use TestClient for sync tests, AsyncClient for async
        client = TestClient(app)
        yield client
    
    @pytest.fixture
    def mock_scoring_service(self):
        """Mock scoring service"""
        with patch('app.scoring_service') as mock:
            mock.compute_score = AsyncMock(return_value={
                "score": 750,
                "baseScore": 700,
                "riskBand": 1,
                "explanation": "Low risk: High transaction activity",
                "stakingBoost": 0,
                "oraclePenalty": 0,
                "stakedAmount": 0,
                "stakingTier": 0
            })
            yield mock
    
    @pytest.fixture
    def mock_blockchain_service(self):
        """Mock blockchain service"""
        with patch('app.blockchain_service') as mock:
            mock.update_score = AsyncMock(return_value="0x" + "a" * 64)
            yield mock
    
    def test_generate_score_success(self, client, mock_scoring_service, mock_blockchain_service):
        """Test successful score generation"""
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            response = client.post(
                "/api/score",
                json={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["score"] == 750
            assert data["riskBand"] == 1
            assert "explanation" in data
    
    def test_generate_score_with_wallet_signature(self, client, mock_scoring_service, mock_blockchain_service):
        """Test score generation with wallet signature"""
        import time
        from tests.fixtures.wallet import create_test_account, create_test_signature
        from utils.wallet_verification import create_verification_message
        
        account = create_test_account()
        timestamp = int(time.time())
        message = create_verification_message(account.address, "generate_score", timestamp)
        signature = create_test_signature(account, message)
        
        response = client.post(
            "/api/score",
            json={
                "address": account.address,
                "signature": signature,
                "message": message,
                "timestamp": timestamp
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
    
    def test_generate_score_invalid_address(self, client):
        """Test score generation with invalid address"""
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            response = client.post(
                "/api/score",
                json={"address": "invalid_address"}
            )
            
            assert response.status_code == 422  # Validation error
    
    def test_generate_score_no_auth(self, client):
        """Test score generation without authentication"""
        response = client.post(
            "/api/score",
            json={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"}
        )
        
        assert response.status_code == 401
    
    def test_generate_score_invalid_signature(self, client, mock_scoring_service):
        """Test score generation with invalid wallet signature"""
        import time
        from utils.wallet_verification import create_verification_message
        
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        timestamp = int(time.time())
        message = create_verification_message(address, "generate_score", timestamp)
        invalid_signature = "0x" + "0" * 130
        
        response = client.post(
            "/api/score",
            json={
                "address": address,
                "signature": invalid_signature,
                "message": message,
                "timestamp": timestamp
            }
        )
        
        assert response.status_code == 401
    
    def test_generate_score_blockchain_error(self, client, mock_scoring_service):
        """Test score generation when blockchain update fails"""
        with patch('app.blockchain_service') as mock_blockchain:
            mock_blockchain.update_score = AsyncMock(side_effect=Exception("Blockchain error"))
            
            with patch('middleware.auth.get_current_user', return_value="test_user"):
                response = client.post(
                    "/api/score",
                    json={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"}
                )
                
                # Should still return 200, but without tx_hash
                assert response.status_code == 200
                data = response.json()
                assert data.get("transactionHash") is None


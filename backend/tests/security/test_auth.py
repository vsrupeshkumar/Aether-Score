"""
Security tests for authentication
"""
import pytest
from httpx import AsyncClient
from app import app


@pytest.fixture
async def client():
    """Create async test client"""
    from httpx import AsyncClient
    async with AsyncClient(base_url="http://test", app=app) as ac:
        yield ac


@pytest.mark.security
class TestAuth:
    """Test authentication security"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ("POST", "/api/score", {"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"}),
            ("POST", "/api/chat", {"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0", "message": "test"}),
        ]
        
        for method, endpoint, data in protected_endpoints:
            if method == "POST":
                response = await client.post(endpoint, json=data)
            else:
                response = await client.get(endpoint)
            
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, client):
        """Test with invalid API key"""
        response = await client.post(
            "/api/score",
            json={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"},
            headers={"Authorization": "ApiKey invalid-key-here"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_jwt_token(self, client):
        """Test with invalid JWT token"""
        response = await client.post(
            "/api/score",
            json={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"},
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_expired_jwt_token(self, client):
        """Test with expired JWT token"""
        # Create an expired token (would need to mock time)
        # For now, we test the structure
        response = await client.post(
            "/api/score",
            json={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"},
            headers={"Authorization": "Bearer expired.token.here"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_wallet_signature_replay_attack(self, client):
        """Test replay attack prevention"""
        import time
        from tests.fixtures.wallet import create_test_account, create_test_signature
        from utils.wallet_verification import create_verification_message
        
        account = create_test_account()
        old_timestamp = int(time.time()) - 400  # 400 seconds ago (expired)
        message = create_verification_message(account.address, "generate_score", old_timestamp)
        signature = create_test_signature(account, message)
        
        response = await client.post(
            "/api/score",
            json={
                "address": account.address,
                "signature": signature,
                "message": message,
                "timestamp": old_timestamp
            }
        )
        
        # Should reject expired signature
        assert response.status_code == 401


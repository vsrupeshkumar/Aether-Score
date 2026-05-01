"""
Integration tests for /api/auth/token endpoint
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient
from app import app


@pytest.mark.integration
class TestAPIAuth:
    """Test /api/auth/token endpoint"""
    
    @pytest.fixture
    async def client(self):
        """Create async test client"""
        from httpx import AsyncClient
        async with AsyncClient(base_url="http://test", app=app) as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_create_token_success(self, client):
        """Test successful token creation"""
        from tests.fixtures.wallet import create_test_account, create_test_signature
        from utils.wallet_verification import create_verification_message
        import time
        
        account = create_test_account()
        timestamp = int(time.time())
        message = create_verification_message(account.address, "auth", timestamp)
        signature = create_test_signature(account, message)
        
        response = await client.post(
            "/api/auth/token",
            json={
                "address": account.address,
                "message": message,
                "signature": signature
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @pytest.mark.asyncio
    async def test_create_token_invalid_signature(self, client):
        """Test token creation with invalid signature"""
        response = await client.post(
            "/api/auth/token",
            json={
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                "message": "Test message",
                "signature": "0x" + "0" * 130
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_token_wrong_address(self, client):
        """Test token creation with wrong address"""
        from tests.fixtures.wallet import create_test_account, create_test_signature
        from utils.wallet_verification import create_verification_message
        import time
        
        account = create_test_account()
        timestamp = int(time.time())
        message = create_verification_message(account.address, "auth", timestamp)
        signature = create_test_signature(account, message)
        
        # Use different address
        wrong_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        response = await client.post(
            "/api/auth/token",
            json={
                "address": wrong_address,
                "message": message,
                "signature": signature
            }
        )
        
        assert response.status_code == 401


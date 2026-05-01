"""
Integration tests for /api/chat endpoint
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from app import app


@pytest.mark.integration
class TestAPIChat:
    """Test /api/chat endpoint"""
    
    @pytest.fixture
    async def client(self):
        """Create async test client"""
        from httpx import AsyncClient
        async with AsyncClient(base_url="http://test", app=app) as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_chat_success(self, client):
        """Test successful chat message"""
        with patch('app.NeuroLendAgent') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.chat.return_value = {
                "response": "Hello! I can help you with a loan.",
                "loanOffer": None
            }
            mock_agent_class.return_value = mock_agent
            
            with patch('middleware.auth.get_current_user', return_value="test_user"):
                response = await client.post(
                    "/api/chat",
                    json={
                        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                        "message": "I need a loan"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
    
    @pytest.mark.asyncio
    async def test_chat_with_loan_offer(self, client):
        """Test chat that generates loan offer"""
        with patch('app.NeuroLendAgent') as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.chat.return_value = {
                "response": "I can offer you a loan!",
                "loanOffer": {
                    "principal": "1000000000000000000",
                    "interestRate": "500",
                    "duration": 30,
                    "collateralRequired": "500000000000000000"
                }
            }
            mock_agent_class.return_value = mock_agent
            
            with patch('middleware.auth.get_current_user', return_value="test_user"):
                response = await client.post(
                    "/api/chat",
                    json={
                        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                        "message": "I want to borrow 1 ETH"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "loanOffer" in data
                assert data["loanOffer"] is not None
    
    @pytest.mark.asyncio
    async def test_chat_invalid_address(self, client):
        """Test chat with invalid address"""
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            response = await client.post(
                "/api/chat",
                json={
                    "address": "invalid_address",
                    "message": "Hello"
                }
            )
            
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_chat_message_too_long(self, client):
        """Test chat with message that's too long"""
        long_message = "a" * 2000
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            response = await client.post(
                "/api/chat",
                json={
                    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                    "message": long_message
                }
            )
            
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_chat_no_auth(self, client):
        """Test chat without authentication"""
        response = await client.post(
            "/api/chat",
            json={
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                "message": "Hello"
            }
        )
        
        assert response.status_code == 401


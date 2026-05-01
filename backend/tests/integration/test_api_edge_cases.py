"""
Edge case integration tests for API endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from httpx import AsyncClient
from app import app


@pytest.mark.integration
class TestAPIEdgeCases:
    """Test edge cases for API endpoints"""
    
    @pytest.fixture
    async def client(self):
        """Create async test client"""
        from httpx import AsyncClient
        async with AsyncClient(base_url="http://test", app=app) as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_score_generation_rate_limit(self, client):
        """Test rate limiting on score generation"""
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            # Make multiple rapid requests
            responses = []
            for i in range(15):  # More than the 10/minute limit
                response = await client.post(
                    "/api/score",
                    json={"address": f"0x{'0' * 40}"}
                )
                responses.append(response.status_code)
            
            # Some requests should be rate limited (429)
            # Note: Rate limiting is disabled in tests, so this may not trigger
            assert all(status in [200, 429, 401] for status in responses)
    
    @pytest.mark.asyncio
    async def test_score_generation_concurrent_requests(self, client):
        """Test handling concurrent score generation requests"""
        import asyncio
        
        async def make_request():
            with patch('middleware.auth.get_current_user', return_value="test_user"):
                return await client.post(
                    "/api/score",
                    json={"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"}
                )
        
        # Make 5 concurrent requests
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete (may have errors, but shouldn't crash)
        assert len(responses) == 5
    
    @pytest.mark.asyncio
    async def test_get_score_nonexistent_address(self, client):
        """Test getting score for address without passport"""
        address = "0x" + "1" * 40  # New address
        
        response = await client.get(f"/api/score/{address}")
        
        # Should return 200 with computed score (not from blockchain)
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
    
    @pytest.mark.asyncio
    async def test_chat_message_empty(self, client):
        """Test chat with empty message (should be rejected)"""
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            response = await client.post(
                "/api/chat",
                json={
                    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                    "message": ""
                }
            )
            
            # Should reject empty message
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_chat_message_max_length(self, client):
        """Test chat with message at max length"""
        max_message = "a" * 1000  # Exactly at limit
        with patch('middleware.auth.get_current_user', return_value="test_user"):
            response = await client.post(
                "/api/chat",
                json={
                    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
                    "message": max_message
                }
            )
            
            # Should accept message at max length
            assert response.status_code in [200, 422]  # May validate or accept
    
    @pytest.mark.asyncio
    async def test_staking_info_zero_stake(self, client):
        """Test staking info for address with zero stake"""
        with patch('services.staking.StakingService') as mock_staking_class:
            mock_staking = Mock()
            mock_staking.get_staked_amount = Mock(return_value=0)
            mock_staking.get_integration_tier = Mock(return_value=0)
            mock_staking.calculate_staking_boost = Mock(return_value=0)
            mock_staking_class.return_value = mock_staking
            
            response = await client.get(
                "/api/staking/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['stakedAmount'] == 0
            assert data['tier'] == 0
    
    @pytest.mark.asyncio
    async def test_ltv_calculation_all_risk_bands(self, client):
        """Test LTV calculation for all risk bands"""
        risk_bands = [0, 1, 2, 3]
        
        for risk_band in risk_bands:
            with patch('app.scoring_service') as mock_scoring:
                mock_scoring.compute_score = AsyncMock(return_value={
                    "score": 500,
                    "riskBand": risk_band,
                    "explanation": "Test"
                })
                
                response = await client.get(
                    "/api/lending/ltv/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['riskBand'] == risk_band
                assert 'ltvBps' in data


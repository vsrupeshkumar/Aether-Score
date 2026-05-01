"""
Integration tests for staking and oracle endpoints
"""
import pytest
from unittest.mock import patch, Mock
from httpx import AsyncClient
from app import app


@pytest.mark.integration
class TestAPIStaking:
    """Test staking and oracle endpoints"""
    
    @pytest.fixture
    async def client(self):
        """Create async test client"""
        from httpx import AsyncClient
        async with AsyncClient(base_url="http://test", app=app) as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_get_staking_info_success(self, client):
        """Test successful staking info retrieval"""
        with patch('services.staking.StakingService') as mock_staking_class:
            mock_staking = Mock()
            mock_staking.get_staked_amount = Mock(return_value=5000000000000000000)
            mock_staking.get_integration_tier = Mock(return_value=2)
            mock_staking.calculate_staking_boost = Mock(return_value=150)
            mock_staking_class.return_value = mock_staking
            
            response = await client.get(
                "/api/staking/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "stakedAmount" in data
            assert "tier" in data
            assert "scoreBoost" in data
            assert data["tier"] == 2
            assert data["scoreBoost"] == 150
    
    @pytest.mark.asyncio
    async def test_get_staking_info_invalid_address(self, client):
        """Test staking info with invalid address"""
        response = await client.get("/api/staking/invalid_address")
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_oracle_price_configured(self, client):
        """Test oracle price when configured"""
        with patch.dict('os.environ', {'QIE_ORACLE_USD_ADDR': '0x' + '1' * 40}):
            with patch('services.oracle.QIEOracleService') as mock_oracle_class:
                mock_oracle = Mock()
                mock_oracle.fetchOraclePrice = AsyncMock(return_value=2000.0)
                mock_oracle_class.return_value = mock_oracle
                
                response = await client.get("/api/oracle/price")
                
                assert response.status_code == 200
                data = response.json()
                assert "price" in data
                assert data["price"] == 2000.0
    
    @pytest.mark.asyncio
    async def test_get_oracle_price_not_configured(self, client):
        """Test oracle price when not configured"""
        with patch.dict('os.environ', {'QIE_ORACLE_USD_ADDR': ''}, clear=False):
            response = await client.get("/api/oracle/price")
            
            assert response.status_code == 200
            data = response.json()
            assert data.get("price") is None
            assert "error" in data
    
    @pytest.mark.asyncio
    async def test_get_ltv_success(self, client):
        """Test successful LTV retrieval"""
        with patch('app.scoring_service') as mock_scoring:
            mock_scoring.compute_score = AsyncMock(return_value={
                "score": 750,
                "riskBand": 1,
                "explanation": "Low risk"
            })
            
            response = await client.get(
                "/api/lending/ltv/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "ltvBps" in data
            assert "ltvPercent" in data
            assert "riskBand" in data
            assert data["riskBand"] == 1
            assert data["ltvBps"] == 7000  # 70% for risk band 1
    
    @pytest.mark.asyncio
    async def test_get_ltv_invalid_address(self, client):
        """Test LTV with invalid address"""
        response = await client.get("/api/lending/ltv/invalid_address")
        
        assert response.status_code == 422


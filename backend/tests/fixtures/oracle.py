"""
Oracle test fixtures
"""
from unittest.mock import AsyncMock


def create_mock_oracle_service():
    """Create mock oracle service"""
    mock = AsyncMock()
    mock.get_price = AsyncMock(return_value=2000.0)
    mock.get_volatility = AsyncMock(return_value=0.25)
    mock.fetchOraclePrice = AsyncMock(return_value=2000.0)
    mock.get_forex_rate = AsyncMock(return_value=1.0)
    mock.get_commodity_price = AsyncMock(return_value=None)
    return mock


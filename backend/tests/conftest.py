"""
Pytest configuration and shared fixtures
"""
import os
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("QIE_RPC_URL", "https://rpc1testnet.qie.digital/")
os.environ.setdefault("CREDIT_PASSPORT_NFT_ADDRESS", "0x0000000000000000000000000000000000000000")
os.environ.setdefault("BACKEND_PRIVATE_KEY", "0x" + "0" * 64)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("SECRETS_ENCRYPTION_KEY", "test-encryption-key-32-chars-long!!")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")  # Disable rate limiting in tests

@pytest.fixture
def mock_web3():
    """Mock Web3 instance"""
    mock = Mock()
    mock.eth = Mock()
    mock.eth.get_balance = Mock(return_value=1000000000000000000)  # 1 ETH
    mock.eth.get_transaction_count = Mock(return_value=10)
    mock.eth.get_transaction_receipt = Mock(return_value=Mock(
        transactionHash=b'\x00' * 32,
        gasUsed=100000,
        status=1
    ))
    mock.eth.gas_price = 1000000000  # 1 gwei
    mock.eth.send_raw_transaction = Mock(return_value=b'\x00' * 32)
    mock.eth.wait_for_transaction_receipt = Mock(return_value=Mock(
        transactionHash=b'\x00' * 32,
        gasUsed=100000,
        status=1
    ))
    mock.from_wei = lambda x, unit: x / 1e18
    mock.to_checksum_address = lambda x: x
    return mock

@pytest.fixture
def mock_contract():
    """Mock contract instance"""
    mock = Mock()
    mock.functions = Mock()
    mock.functions.getScore = Mock(return_value=Mock(call=Mock(return_value=(750, 1, 1234567890))))
    mock.functions.mintOrUpdate = Mock(return_value=Mock(
        build_transaction=Mock(return_value={
            'from': '0x' + '0' * 40,
            'nonce': 0,
            'gas': 200000,
            'gasPrice': 1000000000,
        })
    ))
    return mock

@pytest.fixture
def mock_oracle_service():
    """Mock oracle service"""
    mock = AsyncMock()
    mock.get_price = AsyncMock(return_value=2000.0)
    mock.get_volatility = AsyncMock(return_value=0.25)
    mock.fetchOraclePrice = AsyncMock(return_value=2000.0)
    return mock

@pytest.fixture
def mock_staking_service():
    """Mock staking service"""
    mock = Mock()
    mock.get_integration_tier = Mock(return_value=0)
    mock.get_staked_amount = Mock(return_value=0)
    mock.calculate_staking_boost = Mock(return_value=0)
    return mock

@pytest.fixture
def test_wallet_address():
    """Test wallet address"""
    return "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"

@pytest.fixture
def test_wallet_features():
    """Test wallet features"""
    from models.score import WalletFeatures
    return WalletFeatures(
        tx_count=50,
        total_volume=500.0,
        stablecoin_ratio=0.5,
        avg_tx_value=10.0,
        days_active=30,
        unique_contracts=5,
        max_drawdown=0.1,
        volatility=0.2
    )

@pytest.fixture
def app():
    """FastAPI app instance for testing"""
    from app import app
    return app

@pytest.fixture
def client(app):
    """Test client for FastAPI"""
    return TestClient(app)

@pytest.fixture
async def async_client(app):
    """Async test client for FastAPI"""
    from httpx import AsyncClient
    async with AsyncClient(base_url="http://test", app=app) as ac:
        yield ac


"""
Blockchain test fixtures
"""
from unittest.mock import Mock
from web3 import Web3


def create_mock_web3():
    """Create mock Web3 instance"""
    mock = Mock(spec=Web3)
    mock.eth = Mock()
    mock.eth.get_balance = Mock(return_value=1000000000000000000)  # 1 ETH
    mock.eth.get_transaction_count = Mock(return_value=10)
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


def create_mock_contract():
    """Create mock contract instance"""
    mock = Mock()
    mock.functions = Mock()
    
    # Mock getScore
    get_score_mock = Mock()
    get_score_mock.call = Mock(return_value=(750, 1, 1234567890))
    mock.functions.getScore = Mock(return_value=get_score_mock)
    
    # Mock mintOrUpdate
    mint_mock = Mock()
    mint_mock.build_transaction = Mock(return_value={
        'from': '0x' + '0' * 40,
        'nonce': 0,
        'gas': 200000,
        'gasPrice': 1000000000,
    })
    mock.functions.mintOrUpdate = Mock(return_value=mint_mock)
    
    return mock


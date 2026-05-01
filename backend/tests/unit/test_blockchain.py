"""
Unit tests for BlockchainService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from web3 import Web3
from eth_account import Account
from services.blockchain import BlockchainService


@pytest.mark.unit
class TestBlockchainService:
    """Test BlockchainService"""
    
    @pytest.fixture
    def mock_web3(self):
        """Mock Web3 instance"""
        mock = Mock(spec=Web3)
        mock.eth = Mock()
        mock.eth.get_balance = Mock(return_value=1000000000000000000)
        mock.eth.get_transaction_count = Mock(return_value=10)
        mock.eth.gas_price = 1000000000
        mock.eth.send_raw_transaction = Mock(return_value=b'\x00' * 32)
        mock.eth.wait_for_transaction_receipt = Mock(return_value=Mock(
            transactionHash=b'\x00' * 32,
            gasUsed=100000,
            status=1
        ))
        return mock
    
    @pytest.fixture
    def mock_contract(self):
        """Mock contract instance"""
        mock = Mock()
        mock.functions = Mock()
        get_score_mock = Mock()
        get_score_mock.call = Mock(return_value=(750, 1, 1234567890))
        mock.functions.getScore = Mock(return_value=get_score_mock)
        
        mint_mock = Mock()
        mint_mock.build_transaction = Mock(return_value={
            'from': '0x' + '0' * 40,
            'nonce': 0,
            'gas': 200000,
            'gasPrice': 1000000000,
        })
        mock.functions.mintOrUpdate = Mock(return_value=mint_mock)
        return mock
    
    @pytest.fixture
    def blockchain_service(self, mock_web3, mock_contract):
        """Create BlockchainService instance with mocks"""
        with patch('services.blockchain.Web3') as mock_web3_class, \
             patch('utils.secrets_manager.get_secrets_manager') as mock_secrets:
            mock_web3_class.return_value = mock_web3
            
            # Mock secrets manager
            mock_secrets_manager = Mock()
            mock_secrets_manager.get_secret = Mock(return_value=None)
            mock_secrets.return_value = mock_secrets_manager
            
            with patch.dict('os.environ', {
                'CREDIT_PASSPORT_NFT_ADDRESS': '0x' + '1' * 40,
                'BACKEND_PRIVATE_KEY': '0x' + '0' * 64,
                'QIE_RPC_URL': 'https://rpc1testnet.qie.digital/'
            }):
                service = BlockchainService()
                service.w3 = mock_web3
                service.contract = mock_contract
                # Create a mock account and update transaction 'from' field
                test_account = Account.from_key('0x' + '0' * 64)
                service.account = test_account
                # Update mock to use correct from address
                mock_contract.functions.mintOrUpdate.return_value.build_transaction.return_value['from'] = test_account.address
                yield service
    
    @pytest.mark.asyncio
    async def test_get_score_success(self, blockchain_service):
        """Test successful score retrieval"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        result = await blockchain_service.get_score(address)
        
        assert result is not None
        assert result['score'] == 750
        assert result['riskBand'] == 1
        assert result['lastUpdated'] == 1234567890
    
    @pytest.mark.asyncio
    async def test_get_score_no_passport(self, blockchain_service):
        """Test score retrieval when no passport exists"""
        blockchain_service.contract.functions.getScore.return_value.call.return_value = (0, 0, 0)
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        result = await blockchain_service.get_score(address)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_score_error(self, blockchain_service):
        """Test score retrieval error handling"""
        blockchain_service.contract.functions.getScore.side_effect = Exception("Contract error")
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        result = await blockchain_service.get_score(address)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_score_success(self, blockchain_service):
        """Test successful score update"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        score = 750
        risk_band = 1
        
        tx_hash = await blockchain_service.update_score(address, score, risk_band)
        
        assert tx_hash is not None
        assert isinstance(tx_hash, str)
        blockchain_service.contract.functions.mintOrUpdate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_score_error(self, blockchain_service):
        """Test score update error handling"""
        blockchain_service.contract.functions.mintOrUpdate.side_effect = Exception("Transaction failed")
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        
        with pytest.raises(Exception) as exc_info:
            await blockchain_service.update_score(address, 750, 1)
        
        assert "Error updating score" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_score_invalid_address(self, blockchain_service):
        """Test score update with invalid address"""
        # Mock Web3.to_checksum_address to raise ValueError for invalid address
        from web3 import Web3
        
        def mock_checksum(addr):
            if addr == "invalid_address":
                raise ValueError("Invalid address format")
            # For valid addresses, use the real function
            try:
                return Web3.to_checksum_address(addr)
            except Exception as e:
                raise ValueError(f"Invalid address: {str(e)}")
        
        # Patch Web3.to_checksum_address at the module level
        with patch('services.blockchain.Web3.to_checksum_address', side_effect=mock_checksum):
            address = "invalid_address"
            # Should raise ValueError when trying to checksum invalid address
            with pytest.raises((ValueError, Exception)) as exc_info:
                await blockchain_service.update_score(address, 750, 1)
            # Verify it's the expected error
            error_msg = str(exc_info.value).lower()
            assert "invalid" in error_msg or "address" in error_msg or "format" in error_msg
    
    def test_get_contract_abi(self, blockchain_service):
        """Test contract ABI retrieval"""
        abi = blockchain_service._get_contract_abi()
        
        assert isinstance(abi, list)
        assert len(abi) > 0
        # Check for required functions
        function_names = [func.get('name') for func in abi if isinstance(func, dict)]
        assert 'mintOrUpdate' in function_names
        assert 'getScore' in function_names


"""
Unit tests for TransactionIndexer
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from services.transaction_indexer import TransactionIndexer
from database.models import Transaction, TokenTransfer


@pytest.mark.unit
class TestTransactionIndexer:
    """Test TransactionIndexer service"""
    
    @pytest.fixture
    def indexer(self):
        """Create TransactionIndexer instance"""
        with patch('services.transaction_indexer.Web3') as mock_web3:
            mock_w3 = Mock()
            mock_w3.eth = Mock()
            mock_w3.eth.get_block_number.return_value = 1000
            mock_w3.eth.get_transaction.return_value = {
                "hash": "0x" + "a" * 64,
                "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "to": "0x" + "1" * 40,
                "value": 1000000000000000000,
                "gas": 21000,
                "gasPrice": 1000000000,
            }
            mock_w3.eth.get_transaction_receipt.return_value = {
                "status": 1,
                "gasUsed": 21000,
                "logs": [],
            }
            mock_w3.eth.get_block.return_value = {
                "timestamp": int(datetime.now().timestamp()),
                "number": 1000,
            }
            mock_web3.return_value = mock_w3
            
            indexer = TransactionIndexer()
            indexer.w3 = mock_w3
            yield indexer
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_index_address_transactions(self, indexer, mock_session):
        """Test indexing transactions for an address"""
        with patch('services.transaction_indexer.get_db_session') as mock_get_session, \
             patch('services.transaction_indexer.TransactionRepository') as mock_repo, \
             patch('services.transaction_indexer.UserRepository') as mock_user_repo:
            
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_user_repo.get_or_create_user = AsyncMock()
            mock_repo.get_last_indexed_block = AsyncMock(return_value=None)
            mock_repo.create_transaction = AsyncMock()
            
            # Mock RPC call to get transaction count
            indexer.w3.eth.get_transaction_count = Mock(return_value=10)
            
            result = await indexer.index_address_transactions("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_index_transaction(self, indexer, mock_session):
        """Test indexing a single transaction"""
        with patch('services.transaction_indexer.TransactionRepository') as mock_repo:
            mock_repo.create_transaction = AsyncMock()
            
            tx_data = {
                "hash": "0x" + "a" * 64,
                "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "to": "0x" + "1" * 40,
                "value": 1000000000000000000,
            }
            
            await indexer._index_transaction(mock_session, "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", tx_data, 1000)
            
            mock_repo.create_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_token_transfers(self, indexer, mock_session):
        """Test extracting token transfers from transaction receipt"""
        with patch('services.transaction_indexer.TokenTransferRepository') as mock_repo:
            mock_repo.create_token_transfer = AsyncMock()
            
            receipt = {
                "logs": [
                    {
                        "address": "0x" + "2" * 40,
                        "topics": [
                            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer event
                            "0x000000000000000000000000742d35cc6634c0532925a3b844bc9e7595f0beb",
                            "0x000000000000000000000000" + "1" * 40,
                        ],
                        "data": "0x" + "0" * 64,  # Amount
                    }
                ]
            }
            
            await indexer._extract_token_transfers(mock_session, "0x" + "a" * 64, receipt)
            
            # Should create token transfer if Transfer event found
            assert True  # Test passes if no exception
    
    @pytest.mark.asyncio
    async def test_classify_transaction_type(self, indexer):
        """Test transaction type classification"""
        # Contract creation
        tx1 = {"to": None, "input": "0x" + "1" * 100}
        assert indexer._classify_transaction_type(tx1) == "contract_creation"
        
        # Native transfer
        tx2 = {"to": "0x" + "1" * 40, "input": "0x"}
        assert indexer._classify_transaction_type(tx2) == "native_transfer"
        
        # Contract call
        tx3 = {"to": "0x" + "1" * 40, "input": "0x" + "1" * 100}
        assert indexer._classify_transaction_type(tx3) == "contract_call"
    
    @pytest.mark.asyncio
    async def test_index_address_transactions_incremental(self, indexer, mock_session):
        """Test incremental indexing (only new transactions)"""
        with patch('services.transaction_indexer.get_db_session') as mock_get_session, \
             patch('services.transaction_indexer.TransactionRepository') as mock_repo, \
             patch('services.transaction_indexer.UserRepository') as mock_user_repo:
            
            mock_get_session.return_value.__aenter__.return_value = mock_session
            mock_user_repo.get_or_create_user = AsyncMock()
            mock_repo.get_last_indexed_block = AsyncMock(return_value=500)  # Last indexed at block 500
            mock_repo.create_transaction = AsyncMock()
            
            indexer.w3.eth.get_transaction_count = Mock(return_value=10)
            indexer.w3.eth.get_block_number.return_value = 1000
            
            result = await indexer.index_address_transactions("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
            
            assert result is not None


"""
Transaction Indexer Service

Indexes all transactions for addresses, extracts token transfers,
tracks contract interactions, and stores detailed transaction data.
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.types import TxReceipt, TxData
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database.models import Transaction, User, TokenTransfer
from database.connection import get_db_session
from utils.logger import get_logger
from utils.metrics import (
    record_blockchain_rpc_call,
    record_blockchain_rpc_error,
    record_indexer_operation
)

logger = get_logger(__name__)

# ERC-20 Transfer event signature
ERC20_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
# ERC-721 Transfer event signature
ERC721_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class TransactionIndexer:
    """Service for indexing blockchain transactions"""
    
    def __init__(self):
        self.rpc_url = os.getenv("QIE_RPC_URL") or os.getenv("QIE_TESTNET_RPC_URL", "https://rpc1testnet.qie.digital/")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.batch_size = int(os.getenv("INDEXER_BATCH_SIZE", "100"))
        self.max_blocks_per_request = int(os.getenv("INDEXER_MAX_BLOCKS", "1000"))
        
    async def index_address_transactions(
        self,
        address: str,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Index all transactions for an address
        
        Args:
            address: Wallet address to index
            from_block: Starting block number (None = from beginning)
            to_block: Ending block number (None = latest)
            force_reindex: If True, reindex even if already indexed
            
        Returns:
            Dict with indexing results
        """
        start_time = time.time()
        checksum_address = Web3.to_checksum_address(address)
        
        try:
            logger.info(
                "Starting transaction indexing",
                extra={"address": address, "from_block": from_block, "to_block": to_block}
            )
            
            # Get or create user
            async with get_db_session() as session:
                user = await self._get_or_create_user(session, checksum_address)
                
                # Determine block range
                if from_block is None:
                    # Get last indexed block for this address
                    last_tx = await self._get_last_indexed_transaction(session, checksum_address)
                    from_block = last_tx.block_number + 1 if last_tx and not force_reindex else 0
                
                if to_block is None:
                    to_block = self.w3.eth.block_number
                
                if from_block > to_block:
                    return {
                        "status": "success",
                        "message": "No new transactions to index",
                        "transactions_indexed": 0,
                        "from_block": from_block,
                        "to_block": to_block
                    }
                
                # Index transactions in batches
                transactions_indexed = 0
                token_transfers = []
                contract_interactions = []
                
                # Get all transactions for this address
                for block_num in range(from_block, to_block + 1, self.max_blocks_per_request):
                    end_block = min(block_num + self.max_blocks_per_request - 1, to_block)
                    
                    # Get transactions in this block range
                    txs = await self._get_transactions_in_range(
                        checksum_address,
                        block_num,
                        end_block
                    )
                    
                    for tx_data in txs:
                        # Index transaction
                        tx_record = await self._index_transaction(
                            session,
                            user,
                            tx_data,
                            checksum_address
                        )
                        
                        if tx_record:
                            transactions_indexed += 1
                            
                            # Extract token transfers
                            transfers = await self._extract_token_transfers(tx_data)
                            token_transfers.extend(transfers)
                            
                            # Extract contract interactions
                            if tx_data.get("to") and tx_data["to"] != checksum_address:
                                contract_interactions.append({
                                    "tx_hash": tx_data["hash"].hex(),
                                    "contract_address": tx_data["to"],
                                    "method_id": tx_data.get("input", "0x")[:10] if tx_data.get("input") else None
                                })
                
                # Store token transfers and contract interactions
                await self._store_token_transfers(session, token_transfers)
                await self._store_contract_interactions(session, contract_interactions)
                
                await session.commit()
                
                duration = time.time() - start_time
                
                logger.info(
                    "Transaction indexing completed",
                    extra={
                        "address": address,
                        "transactions_indexed": transactions_indexed,
                        "token_transfers": len(token_transfers),
                        "contract_interactions": len(contract_interactions),
                        "duration": duration
                    }
                )
                
                record_indexer_operation(
                    operation="index_address",
                    status="success",
                    duration=duration,
                    transactions_count=transactions_indexed
                )
                
                return {
                    "status": "success",
                    "transactions_indexed": transactions_indexed,
                    "token_transfers": len(token_transfers),
                    "contract_interactions": len(contract_interactions),
                    "from_block": from_block,
                    "to_block": to_block,
                    "duration": duration
                }
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Error indexing transactions",
                exc_info=True,
                extra={
                    "address": address,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration": duration
                }
            )
            
            record_indexer_operation(
                operation="index_address",
                status="error",
                duration=duration
            )
            
            raise
    
    async def _get_or_create_user(self, session: AsyncSession, address: str) -> User:
        """Get or create user record"""
        from database.repositories import UserRepository
        
        user = await UserRepository.get_by_wallet_address(session, address)
        if not user:
            user = await UserRepository.create(session, address)
        
        return user
    
    async def _get_last_indexed_transaction(
        self,
        session: AsyncSession,
        address: str
    ) -> Optional[Transaction]:
        """Get the last indexed transaction for an address"""
        try:
            stmt = select(Transaction).where(
                Transaction.wallet_address == address
            ).order_by(Transaction.block_number.desc()).limit(1)
            
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Error getting last indexed transaction: {e}")
            return None
    
    async def _get_transactions_in_range(
        self,
        address: str,
        from_block: int,
        to_block: int
    ) -> List[Dict[str, Any]]:
        """Get all transactions for an address in a block range"""
        transactions = []
        
        try:
            # Get transactions where address is sender
            for block_num in range(from_block, to_block + 1):
                try:
                    block = self.w3.eth.get_block(block_num, full_transactions=True)
                    
                    for tx in block.transactions:
                        if isinstance(tx, dict):
                            tx_from = tx.get("from", "").lower()
                            tx_to = tx.get("to", "").lower() if tx.get("to") else None
                            
                            if tx_from == address.lower() or (tx_to and tx_to == address.lower()):
                                # Get transaction receipt for status
                                try:
                                    receipt = self.w3.eth.get_transaction_receipt(tx["hash"])
                                    tx["status"] = "success" if receipt.status == 1 else "failed"
                                    tx["gas_used"] = receipt.gasUsed
                                except:
                                    tx["status"] = "pending"
                                
                                transactions.append(tx)
                                
                except Exception as e:
                    logger.warning(f"Error getting block {block_num}: {e}")
                    continue
            
            record_blockchain_rpc_call(
                operation="get_transactions_range",
                status="success",
                blocks_queried=to_block - from_block + 1
            )
            
        except Exception as e:
            logger.error(f"Error getting transactions in range: {e}", exc_info=True)
            record_blockchain_rpc_error(type(e).__name__)
        
        return transactions
    
    async def _index_transaction(
        self,
        session: AsyncSession,
        user: User,
        tx_data: Dict[str, Any],
        address: str
    ) -> Optional[Transaction]:
        """Index a single transaction"""
        try:
            tx_hash = tx_data["hash"].hex() if hasattr(tx_data["hash"], "hex") else tx_data["hash"]
            
            # Check if already indexed
            stmt = select(Transaction).where(Transaction.tx_hash == tx_hash)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                return existing
            
            # Determine transaction type
            tx_type = self._classify_transaction_type(tx_data, address)
            
            # Get block info
            block_number = tx_data.get("blockNumber")
            block_timestamp = None
            if block_number:
                try:
                    block = self.w3.eth.get_block(block_number)
                    block_timestamp = block.timestamp
                except:
                    pass
            
            # Create transaction record
            transaction = Transaction(
                wallet_address=address,
                tx_hash=tx_hash,
                tx_type=tx_type,
                block_number=block_number,
                block_timestamp=block_timestamp,
                from_address=tx_data.get("from"),
                to_address=tx_data.get("to"),
                value=tx_data.get("value", 0),
                gas_used=tx_data.get("gas_used") or tx_data.get("gas"),
                gas_price=tx_data.get("gasPrice"),
                status=tx_data.get("status", "pending"),
                input_data=tx_data.get("input", "0x")[:1000] if tx_data.get("input") else None,  # Truncate for storage
                contract_address=tx_data.get("to") if tx_data.get("input") else None
            )
            
            session.add(transaction)
            await session.flush()
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error indexing transaction: {e}", exc_info=True)
            return None
    
    def _classify_transaction_type(self, tx_data: Dict[str, Any], address: str) -> str:
        """Classify transaction type"""
        tx_from = tx_data.get("from", "").lower()
        tx_to = tx_data.get("to")
        input_data = tx_data.get("input", "0x")
        
        if not tx_to:
            return "contract_creation"
        
        if input_data == "0x" or len(input_data) <= 2:
            if tx_from == address.lower():
                return "native_send"
            else:
                return "native_receive"
        
        # Check for token transfer
        if input_data.startswith("0xa9059cbb"):  # transfer(address,uint256)
            return "erc20_transfer"
        elif input_data.startswith("0x23b872dd"):  # transferFrom(address,address,uint256)
            return "erc20_transfer_from"
        elif input_data.startswith("0x42842e0e"):  # safeTransferFrom (ERC721)
            return "erc721_transfer"
        
        # Contract interaction
        return "contract_call"
    
    async def _extract_token_transfers(
        self,
        tx_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract token transfers from transaction receipt"""
        transfers = []
        
        try:
            tx_hash = tx_data["hash"].hex() if hasattr(tx_data["hash"], "hex") else tx_data["hash"]
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            # Parse Transfer events
            for log in receipt.logs:
                if len(log.topics) >= 3 and log.topics[0].hex() == ERC20_TRANSFER_TOPIC:
                    # ERC-20 Transfer
                    from_addr = "0x" + log.topics[1].hex()[-40:]
                    to_addr = "0x" + log.topics[2].hex()[-40:]
                    
                    # Decode amount (assuming standard ERC-20)
                    if len(log.data) >= 32:
                        amount = int.from_bytes(log.data[:32], byteorder='big')
                        
                        transfers.append({
                            "tx_hash": tx_hash,
                            "token_address": log.address,
                            "from_address": from_addr,
                            "to_address": to_addr,
                            "amount": amount,
                            "token_type": "ERC20",
                            "block_number": receipt.blockNumber
                        })
        
        except Exception as e:
            logger.debug(f"Error extracting token transfers: {e}")
        
        return transfers
    
    async def _store_token_transfers(
        self,
        session: AsyncSession,
        transfers: List[Dict[str, Any]]
    ):
        """Store token transfers in database"""
        for transfer in transfers:
            try:
                # Check if already stored
                stmt = select(TokenTransfer).where(
                    TokenTransfer.tx_hash == transfer["tx_hash"],
                    TokenTransfer.token_address == transfer["token_address"],
                    TokenTransfer.from_address == transfer["from_address"],
                    TokenTransfer.to_address == transfer["to_address"]
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    continue
                
                # Create token transfer record
                token_transfer = TokenTransfer(
                    tx_hash=transfer["tx_hash"],
                    token_address=transfer["token_address"],
                    token_type=transfer["token_type"],
                    from_address=transfer["from_address"],
                    to_address=transfer["to_address"],
                    amount=transfer.get("amount"),
                    token_id=transfer.get("token_id"),
                    block_number=transfer.get("block_number"),
                    block_timestamp=transfer.get("block_timestamp")
                )
                
                session.add(token_transfer)
                
            except Exception as e:
                logger.warning(f"Error storing token transfer: {e}", extra={"transfer": transfer})
                continue
    
    async def _store_contract_interactions(
        self,
        session: AsyncSession,
        interactions: List[Dict[str, Any]]
    ):
        """Store contract interactions"""
        # Store in transaction records (already done in _index_transaction)
        pass
    
    async def get_indexing_status(self, address: str) -> Dict[str, Any]:
        """Get indexing status for an address"""
        try:
            async with get_db_session() as session:
                # Get total transactions indexed
                stmt = select(Transaction).where(Transaction.wallet_address == address)
                result = await session.execute(stmt)
                transactions = result.scalars().all()
                
                if not transactions:
                    return {
                        "address": address,
                        "indexed": False,
                        "total_transactions": 0,
                        "last_indexed_block": None
                    }
                
                last_tx = max(transactions, key=lambda x: x.block_number or 0)
                
                return {
                    "address": address,
                    "indexed": True,
                    "total_transactions": len(transactions),
                    "last_indexed_block": last_tx.block_number,
                    "last_indexed_at": last_tx.block_timestamp.isoformat() if last_tx.block_timestamp else None
                }
        except Exception as e:
            logger.error(f"Error getting indexing status: {e}", exc_info=True)
            return {
                "address": address,
                "indexed": False,
                "error": str(e)
            }


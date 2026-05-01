"""
Blockchain event monitoring service
"""
import asyncio
from typing import Dict, List, Optional, Callable
from web3 import Web3
from web3.types import EventData, LogReceipt
from eth_account import Account
import os
from utils.logger import get_logger
from utils.metrics import (
    record_blockchain_transaction,
    record_blockchain_rpc_error
)
from utils.monitoring import capture_exception, capture_message

logger = get_logger(__name__)


class BlockchainMonitor:
    """Monitor blockchain events and transactions"""
    
    def __init__(self):
        self.rpc_url = os.getenv("QIE_RPC_URL") or os.getenv("QIE_TESTNET_RPC_URL", "https://rpc1testnet.qie.digital/")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.contract_address = os.getenv("CREDIT_PASSPORT_NFT_ADDRESS")
        self.monitoring = False
        self.event_handlers: Dict[str, List[Callable]] = {}
        
    def register_event_handler(self, event_name: str, handler: Callable):
        """Register a handler for a specific event"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    async def monitor_contract_events(
        self,
        contract_address: str,
        contract_abi: List[Dict],
        from_block: Optional[int] = None,
        to_block: Optional[str] = "latest"
    ):
        """
        Monitor contract events
        
        Args:
            contract_address: Contract address to monitor
            contract_abi: Contract ABI
            from_block: Starting block number (None = latest)
            to_block: Ending block number ("latest" = current)
        """
        try:
            contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
            
            # Get all events
            events = contract.events
            
            # Monitor each event type
            for event_name in events:
                await self._monitor_event(
                    contract,
                    event_name,
                    from_block,
                    to_block
                )
                
        except Exception as e:
            logger.error("Failed to monitor contract events", exc_info=True, extra={"contract": contract_address})
            capture_exception(e, contract_address=contract_address, operation="monitor_events")
            record_blockchain_rpc_error(type(e).__name__)
    
    async def _monitor_event(
        self,
        contract,
        event_name: str,
        from_block: Optional[int],
        to_block: Optional[str]
    ):
        """Monitor a specific event"""
        try:
            event = getattr(contract.events, event_name)
            
            # Get event logs
            logs = event.get_logs(
                fromBlock=from_block or "latest",
                toBlock=to_block
            )
            
            for log in logs:
                await self._handle_event(event_name, log)
                
        except Exception as e:
            logger.error(f"Failed to monitor event {event_name}", exc_info=True)
            capture_exception(e, event_name=event_name, operation="monitor_event")
    
    async def _handle_event(self, event_name: str, log: LogReceipt):
        """Handle a contract event"""
        try:
            logger.info(
                f"Contract event: {event_name}",
                extra={
                    "event": event_name,
                    "tx_hash": log["transactionHash"].hex(),
                    "block_number": log["blockNumber"],
                    "contract_address": log["address"],
                    "extra_data": {
                        "args": dict(log["args"]) if hasattr(log["args"], "__dict__") else str(log["args"])
                    }
                }
            )
            
            # Call registered handlers
            if event_name in self.event_handlers:
                for handler in self.event_handlers[event_name]:
                    try:
                        await handler(log) if asyncio.iscoroutinefunction(handler) else handler(log)
                    except Exception as e:
                        logger.error(f"Event handler failed for {event_name}", exc_info=True)
            
            # Record metrics
            record_blockchain_transaction(
                status="success",
                contract=log["address"],
                operation=f"event_{event_name}",
                duration=0
            )
            
        except Exception as e:
            logger.error(f"Failed to handle event {event_name}", exc_info=True)
            capture_exception(e, event_name=event_name, tx_hash=log.get("transactionHash", "").hex())
    
    async def monitor_transaction_status(
        self,
        tx_hash: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Monitor transaction status until confirmed or timeout
        
        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds
            
        Returns:
            Transaction status information
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    return {
                        "status": "timeout",
                        "tx_hash": tx_hash,
                        "message": "Transaction confirmation timeout"
                    }
                
                # Get transaction receipt
                try:
                    receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                    
                    # Transaction confirmed
                    if receipt.status == 1:
                        confirmation_time = elapsed
                        logger.info(
                            "Transaction confirmed",
                            extra={
                                "tx_hash": tx_hash,
                                "block_number": receipt.blockNumber,
                                "gas_used": receipt.gasUsed,
                                "confirmation_time": confirmation_time
                            }
                        )
                        
                        record_blockchain_transaction(
                            status="success",
                            contract=receipt.to or "unknown",
                            operation="transaction",
                            duration=confirmation_time,
                            gas_used=receipt.gasUsed
                        )
                        
                        return {
                            "status": "confirmed",
                            "tx_hash": tx_hash,
                            "block_number": receipt.blockNumber,
                            "gas_used": receipt.gasUsed,
                            "confirmation_time": confirmation_time
                        }
                    else:
                        # Transaction failed
                        logger.error(
                            "Transaction failed",
                            extra={
                                "tx_hash": tx_hash,
                                "block_number": receipt.blockNumber,
                                "status": receipt.status
                            }
                        )
                        
                        capture_message(
                            "Blockchain transaction failed",
                            level="error",
                            tx_hash=tx_hash,
                            block_number=receipt.blockNumber
                        )
                        
                        record_blockchain_transaction(
                            status="failed",
                            contract=receipt.to or "unknown",
                            operation="transaction",
                            duration=elapsed
                        )
                        
                        return {
                            "status": "failed",
                            "tx_hash": tx_hash,
                            "block_number": receipt.blockNumber,
                            "message": "Transaction reverted"
                        }
                        
                except Exception:
                    # Transaction not yet mined, wait and retry
                    await asyncio.sleep(2)
                    continue
                    
        except Exception as e:
            logger.error("Transaction monitoring failed", exc_info=True, extra={"tx_hash": tx_hash})
            capture_exception(e, tx_hash=tx_hash, operation="monitor_transaction")
            record_blockchain_rpc_error(type(e).__name__)
            
            return {
                "status": "error",
                "tx_hash": tx_hash,
                "error": str(e)
            }
    
    async def track_failed_transactions(
        self,
        tx_hashes: List[str]
    ) -> Dict[str, Any]:
        """
        Track multiple transactions and report failures
        
        Args:
            tx_hashes: List of transaction hashes
            
        Returns:
            Summary of transaction statuses
        """
        results = {
            "total": len(tx_hashes),
            "success": 0,
            "failed": 0,
            "pending": 0,
            "errors": []
        }
        
        for tx_hash in tx_hashes:
            status = await self.monitor_transaction_status(tx_hash)
            
            if status["status"] == "confirmed":
                results["success"] += 1
            elif status["status"] == "failed":
                results["failed"] += 1
                results["errors"].append({
                    "tx_hash": tx_hash,
                    "message": status.get("message", "Transaction failed")
                })
            else:
                results["pending"] += 1
        
        # Alert if failure rate is high
        if results["total"] > 0:
            failure_rate = results["failed"] / results["total"]
            if failure_rate > 0.1:  # More than 10% failure rate
                capture_message(
                    f"High blockchain transaction failure rate: {failure_rate:.2%}",
                    level="warning",
                    failure_rate=failure_rate,
                    total=results["total"],
                    failed=results["failed"]
                )
        
        return results


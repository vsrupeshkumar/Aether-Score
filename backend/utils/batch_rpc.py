"""
Batch RPC call utilities with deduplication and optimization
"""
from typing import List, Dict, Any, Set
from collections import defaultdict
from utils.rpc_pool import batch_rpc_call, optimized_rpc_call
from utils.logger import get_logger

logger = get_logger(__name__)


class BatchRPCHandler:
    """Handler for batch RPC calls with deduplication"""
    
    def __init__(self):
        self.pending_calls: Dict[str, List[Dict]] = defaultdict(list)
        self.call_ids: Dict[str, int] = {}
    
    def add_call(self, method: str, params: dict, call_id: str = None) -> str:
        """
        Add RPC call to batch
        
        Args:
            method: RPC method name
            params: Parameter dictionary
            call_id: Optional call ID (auto-generated if not provided)
            
        Returns:
            Call ID
        """
        if call_id is None:
            call_id = f"{method}_{len(self.pending_calls[method])}"
        
        # Check for duplicates
        params_key = str(sorted(params.items()))
        if params_key in self.call_ids:
            return self.call_ids[params_key]
        
        self.pending_calls[method].append(params)
        self.call_ids[params_key] = call_id
        
        return call_id
    
    def execute_batch(self, method: str) -> List[Any]:
        """
        Execute batch of RPC calls for a method
        
        Args:
            method: RPC method name
            
        Returns:
            List of results
        """
        if method not in self.pending_calls or not self.pending_calls[method]:
            return []
        
        params_list = self.pending_calls[method]
        results = batch_rpc_call(method, params_list)
        
        # Clear pending calls
        del self.pending_calls[method]
        
        return results
    
    def execute_all(self) -> Dict[str, List[Any]]:
        """
        Execute all pending batch calls
        
        Returns:
            Dictionary mapping methods to results
        """
        results = {}
        for method in list(self.pending_calls.keys()):
            results[method] = self.execute_batch(method)
        return results


def deduplicate_rpc_calls(calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate RPC calls based on method and parameters
    
    Args:
        calls: List of call dictionaries with 'method' and 'params'
        
    Returns:
        Deduplicated list of calls
    """
    seen: Set[str] = set()
    deduplicated = []
    
    for call in calls:
        method = call.get("method")
        params = call.get("params", {})
        key = f"{method}:{str(sorted(params.items()) if isinstance(params, dict) else params)}"
        
        if key not in seen:
            seen.add(key)
            deduplicated.append(call)
    
    return deduplicated


def batch_get_scores(addresses: List[str], contract_abi: List[Dict]) -> List[Dict]:
    """
    Batch get scores from blockchain for multiple addresses
    
    Args:
        addresses: List of wallet addresses
        contract_abi: Contract ABI
        
    Returns:
        List of score dictionaries
    """
    if not addresses:
        return []
    
    # Deduplicate addresses
    unique_addresses = list(set(addresses))
    
    # Prepare batch calls
    calls = []
    for address in unique_addresses:
        calls.append({
            "method": "eth_call",
            "params": {
                "to": contract_abi,  # Contract address
                "data": f"getScore({address})"  # Function call data
            }
        })
    
    # Deduplicate calls
    deduplicated = deduplicate_rpc_calls(calls)
    
    # Execute batch
    results = batch_rpc_call("eth_call", [call["params"] for call in deduplicated])
    
    # Map results back to addresses
    score_map = {}
    for i, result in enumerate(results):
        if i < len(unique_addresses):
            score_map[unique_addresses[i]] = result
    
    # Return in original order
    return [score_map.get(addr, None) for addr in addresses]


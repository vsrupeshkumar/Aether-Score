"""
Web3 RPC connection pooling for optimized blockchain calls with failover support
"""
import os
from typing import Optional, List
from web3 import Web3
from web3.providers import HTTPProvider
from utils.logger import get_logger
from utils.cache import get_cached_rpc_result, cache_rpc_result
from config.network import get_network_config, get_healthy_rpc_urls

logger = get_logger(__name__)

# Global Web3 instance pool (one per RPC URL)
_rpc_pool: List[Web3] = []
_rpc_urls: List[str] = []
_current_rpc_index = 0
_pool_size = int(os.getenv("RPC_POOL_SIZE", "5"))


def get_rpc_pool() -> List[Web3]:
    """Get or create RPC connection pool with failover support"""
    global _rpc_pool, _rpc_urls
    
    if not _rpc_pool:
        # Get network configuration
        network_config = get_network_config()
        # Get healthy RPC URLs (with fallback to all if health check fails)
        _rpc_urls = get_healthy_rpc_urls(network_config)
        
        # Create pool of Web3 instances (distributed across available RPCs)
        for i in range(_pool_size):
            # Round-robin across available RPC URLs
            rpc_url = _rpc_urls[i % len(_rpc_urls)] if _rpc_urls else network_config.get_primary_rpc()
            provider = HTTPProvider(
                rpc_url,
                request_kwargs={"timeout": 30}  # Increased timeout for mainnet
            )
            w3 = Web3(provider)
            _rpc_pool.append(w3)
        
        logger.info(
            f"RPC pool created with {_pool_size} connections across {len(_rpc_urls)} RPC endpoints",
            extra={
                "rpc_urls": _rpc_urls,
                "network": network_config.name,
            }
        )
    
    return _rpc_pool


def get_rpc_connection() -> Optional[Web3]:
    """Get a Web3 connection from pool (round-robin with failover)"""
    global _current_rpc_index
    
    pool = get_rpc_pool()
    if not pool:
        return None
    
    # Round-robin across pool
    connection = pool[_current_rpc_index % len(pool)]
    _current_rpc_index += 1
    
    return connection


def batch_rpc_call(method: str, params_list: List[dict]) -> List[any]:
    """
    Make batch RPC calls (if supported by provider)
    
    Args:
        method: RPC method name
        params_list: List of parameter dictionaries
        
    Returns:
        List of results
    """
    w3 = get_rpc_connection()
    if not w3:
        return []
    
    try:
        # Check cache for each call
        results = []
        uncached_indices = []
        uncached_params = []
        
        for i, params in enumerate(params_list):
            cached = get_cached_rpc_result(method, params)
            if cached is not None:
                results.append(cached)
            else:
                results.append(None)
                uncached_indices.append(i)
                uncached_params.append(params)
        
        # Make batch RPC call for uncached items
        if uncached_params:
            # Build batch request
            batch_request = []
            for params in uncached_params:
                batch_request.append({
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": [params] if not isinstance(params, list) else params,
                    "id": len(batch_request)
                })
            
            # Make batch call (if provider supports it)
            try:
                # Use Web3's batch call if available
                batch_results = w3.manager.request_blocking("eth_batch", batch_request)
                
                # Process results and cache
                for idx, result, params in zip(uncached_indices, batch_results, uncached_params):
                    if result and "result" in result:
                        results[idx] = result["result"]
                        cache_rpc_result(method, params, result["result"])
                    else:
                        results[idx] = None
            except Exception as e:
                # Fallback to individual calls
                logger.warning(f"Batch RPC call failed, using individual calls: {e}")
                for idx, params in zip(uncached_indices, uncached_params):
                    try:
                        result = w3.manager.request_blocking(method, params)
                        results[idx] = result
                        cache_rpc_result(method, params, result)
                    except Exception as call_error:
                        logger.error(f"RPC call failed: {call_error}", exc_info=True)
                        results[idx] = None
        
        return results
    except Exception as e:
        logger.error(f"Batch RPC call error: {e}", exc_info=True)
        return []


def optimized_rpc_call(method: str, params: dict, use_cache: bool = True) -> Optional[any]:
    """
    Make optimized RPC call with caching and connection pooling
    
    Args:
        method: RPC method name
        params: Parameter dictionary
        use_cache: Whether to use cache
        
    Returns:
        RPC result or None
    """
    # Check cache
    if use_cache:
        cached = get_cached_rpc_result(method, params)
        if cached is not None:
            return cached
    
    # Get connection from pool
    w3 = get_rpc_connection()
    if not w3:
        return None
    
    try:
        # Make RPC call
        result = w3.manager.request_blocking(method, params)
        
        # Cache result
        if use_cache and result is not None:
            cache_rpc_result(method, params, result)
        
        return result
    except Exception as e:
        logger.error(f"RPC call error: {e}", exc_info=True, extra={"method": method})
        return None


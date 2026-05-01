"""
Health check utilities
"""
import asyncio
from typing import Dict, Any, Optional
from web3 import Web3
import os
from utils.logger import get_logger

logger = get_logger(__name__)


async def check_blockchain_rpc() -> Dict[str, Any]:
    """Check blockchain RPC connectivity"""
    try:
        rpc_url = os.getenv("QIE_RPC_URL") or os.getenv("QIE_TESTNET_RPC_URL", "https://rpc1testnet.qie.digital/")
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))
        
        # Try to get latest block
        block_number = w3.eth.block_number
        
        return {
            "status": "healthy",
            "rpc_url": rpc_url,
            "latest_block": block_number,
            "connected": w3.is_connected()
        }
    except Exception as e:
        logger.error("Blockchain RPC check failed", exc_info=True, extra={"error": str(e)})
        return {
            "status": "unhealthy",
            "error": str(e),
            "connected": False
        }


async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity (for rate limiting)"""
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url, socket_connect_timeout=2)
        
        # Try to ping
        r.ping()
        
        return {
            "status": "healthy",
            "connected": True
        }
    except ImportError:
        # Redis not installed, rate limiting might use in-memory store
        return {
            "status": "not_configured",
            "message": "Redis not configured, using in-memory rate limiting"
        }
    except Exception as e:
        logger.warning("Redis check failed", extra={"error": str(e)})
        return {
            "status": "unhealthy",
            "error": str(e),
            "connected": False
        }


async def check_oracle_service() -> Dict[str, Any]:
    """Check oracle service availability"""
    try:
        from services.oracle import QIEOracleService
        oracle_service = QIEOracleService()
        
        # Try to get a price (with timeout)
        price = await asyncio.wait_for(
            oracle_service.get_price("ETH", "crypto"),
            timeout=5.0
        )
        
        return {
            "status": "healthy",
            "price_available": price is not None
        }
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "error": "Oracle service timeout"
        }
    except Exception as e:
        logger.warning("Oracle service check failed", extra={"error": str(e)})
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        from database.connection import check_db_health
        return await check_db_health()
    except ImportError:
        return {
            "status": "not_configured",
            "message": "Database not configured"
        }
    except Exception as e:
        logger.error("Database check failed", exc_info=True, extra={"error": str(e)})
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_all_dependencies() -> Dict[str, Any]:
    """Check all dependencies"""
    blockchain = await check_blockchain_rpc()
    redis = await check_redis()
    oracle = await check_oracle_service()
    database = await check_database()
    
    all_healthy = (
        blockchain.get("status") == "healthy" and
        redis.get("status") in ["healthy", "not_configured"] and
        oracle.get("status") == "healthy" and
        database.get("status") in ["healthy", "not_configured"]
    )
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "dependencies": {
            "blockchain": blockchain,
            "redis": redis,
            "oracle": oracle,
            "database": database
        }
    }


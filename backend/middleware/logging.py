"""
Request logging middleware
"""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from utils.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request_id = request.headers.get("X-Request-ID", correlation_id)
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Start time
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "request_id": request_id,
                "endpoint": f"{request.method} {request.url.path}",
                "ip_address": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown"),
                "extra_data": {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                }
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "endpoint": f"{request.method} {request.url.path}",
                    "ip_address": client_ip,
                    "status_code": response.status_code,
                    "duration_ms": duration * 1000,
                    "extra_data": {
                        "method": request.method,
                        "path": request.url.path,
                    }
                }
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "request_id": request_id,
                    "endpoint": f"{request.method} {request.url.path}",
                    "ip_address": client_ip,
                    "duration_ms": duration * 1000,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "extra_data": {
                        "method": request.method,
                        "path": request.url.path,
                    }
                }
            )
            
            raise


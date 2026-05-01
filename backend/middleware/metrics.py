"""
Metrics collection middleware
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from utils.metrics import (
    record_http_request,
    record_api_request,
    active_requests,
    record_error
)
from utils.logger import get_logger

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next):
        # Increment active requests
        active_requests.inc()
        
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            status_code = response.status_code
            
            # Record HTTP metrics
            record_http_request(method, endpoint, status_code, duration)
            
            # Record API metrics for API endpoints
            if endpoint.startswith("/api/"):
                status = "success" if status_code < 400 else "error"
                record_api_request(endpoint, status, duration)
            
            # Record errors
            if status_code >= 400:
                error_type = f"http_{status_code}"
                record_error(error_type, endpoint)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record error
            error_type = type(e).__name__
            record_error(error_type, endpoint)
            record_http_request(method, endpoint, 500, duration)
            record_api_request(endpoint, "error", duration)
            
            raise
        finally:
            # Decrement active requests
            active_requests.dec()


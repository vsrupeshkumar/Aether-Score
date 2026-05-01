"""
Performance monitoring middleware
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from utils.logger import get_logger
from utils.monitoring import capture_message, add_breadcrumb
from utils.metrics import record_error

logger = get_logger(__name__)

# Performance thresholds
SLOW_REQUEST_THRESHOLD = 1.0  # 1 second
VERY_SLOW_REQUEST_THRESHOLD = 5.0  # 5 seconds


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking slow requests and performance issues"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        endpoint = f"{request.method} {request.url.path}"
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log slow requests
            if duration > VERY_SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    "Very slow request detected",
                    extra={
                        "endpoint": endpoint,
                        "duration": duration,
                        "threshold": VERY_SLOW_REQUEST_THRESHOLD,
                        "status_code": response.status_code,
                        "extra_data": {
                            "method": request.method,
                            "path": request.url.path,
                        }
                    }
                )
                
                # Send to Sentry
                capture_message(
                    f"Very slow request: {endpoint} took {duration:.2f}s",
                    level="warning",
                    endpoint=endpoint,
                    duration=duration,
                    status_code=response.status_code
                )
                
                # Add breadcrumb
                add_breadcrumb(
                    message=f"Slow request: {endpoint}",
                    category="performance",
                    level="warning",
                    data={
                        "duration": duration,
                        "endpoint": endpoint
                    }
                )
                
            elif duration > SLOW_REQUEST_THRESHOLD:
                logger.info(
                    "Slow request detected",
                    extra={
                        "endpoint": endpoint,
                        "duration": duration,
                        "threshold": SLOW_REQUEST_THRESHOLD,
                        "status_code": response.status_code,
                    }
                )
            
            # Add performance header
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log slow error responses
            if duration > SLOW_REQUEST_THRESHOLD:
                logger.error(
                    "Slow error response",
                    exc_info=True,
                    extra={
                        "endpoint": endpoint,
                        "duration": duration,
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    }
                )
            
            raise


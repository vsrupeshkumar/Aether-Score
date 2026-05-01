"""
Distributed Tracing Middleware — Phase 1 Extension

Adds:
  - X-Correlation-ID header propagation (generated if absent)
  - X-Request-ID per request
  - Structured trace context injected into log records
  - Optional OpenTelemetry span creation (graceful fallback)
  - Timing instrumentation (X-Response-Time header)

Integrates with existing LoggingMiddleware and MetricsMiddleware without
replacing them.  Mount BEFORE LoggingMiddleware in app.py so the correlation
ID is available in all subsequent log records.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Context variables — accessible from any coroutine in the same request
# ---------------------------------------------------------------------------

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
span_id_var: ContextVar[str] = ContextVar("span_id", default="")


def get_correlation_id() -> str:
    return correlation_id_var.get()


def get_request_id() -> str:
    return request_id_var.get()


# ---------------------------------------------------------------------------
# Log filter — injects trace IDs into every log record from this request
# ---------------------------------------------------------------------------

class TraceContextFilter(logging.Filter):
    """Injects correlation_id and request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get() or "-"
        record.request_id = request_id_var.get() or "-"
        return True


# Attach filter to root logger once at import time
_filter = TraceContextFilter()
logging.getLogger().addFilter(_filter)


# ---------------------------------------------------------------------------
# OpenTelemetry helper (optional)
# ---------------------------------------------------------------------------

def _try_otel_span(name: str, attributes: dict) -> Optional[object]:
    """Create an OpenTelemetry span if the SDK is installed, else return None."""
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer("aether-score")
        span = tracer.start_span(name)
        for k, v in attributes.items():
            span.set_attribute(k, str(v))
        return span
    except (ImportError, Exception):
        return None


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class TracingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that:
      1. Reads or generates a Correlation-ID for the request
      2. Generates a unique Request-ID
      3. Propagates both IDs into response headers
      4. Records request duration in X-Response-Time (ms)
      5. Optionally creates an OpenTelemetry span
      6. Injects trace context into logging via ContextVar

    Mount in app.py:
        from middleware.tracing import TracingMiddleware
        app.add_middleware(TracingMiddleware)
    """

    CORRELATION_HEADER = "X-Correlation-ID"
    REQUEST_ID_HEADER = "X-Request-ID"
    RESPONSE_TIME_HEADER = "X-Response-Time"

    def __init__(self, app: ASGIApp, propagate_b3: bool = False):
        super().__init__(app)
        self.propagate_b3 = propagate_b3  # set True for B3 (Zipkin/Jaeger) propagation

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()

        # ------------------------------------------------------------------
        # Generate / propagate IDs
        # ------------------------------------------------------------------
        corr_id = (
            request.headers.get(self.CORRELATION_HEADER)
            or request.headers.get("X-B3-TraceId")  # B3 fallback
            or str(uuid.uuid4())
        )
        req_id = str(uuid.uuid4())

        # Store in context vars so any code in this request can access them
        correlation_id_var.set(corr_id)
        request_id_var.set(req_id)

        # ------------------------------------------------------------------
        # Optional OpenTelemetry span
        # ------------------------------------------------------------------
        span = _try_otel_span(
            name=f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "correlation_id": corr_id,
                "request_id": req_id,
            },
        )

        # ------------------------------------------------------------------
        # Process request
        # ------------------------------------------------------------------
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "Unhandled exception",
                extra={"correlation_id": corr_id, "request_id": req_id, "path": request.url.path},
                exc_info=True,
            )
            if span:
                try:
                    span.record_exception(exc)
                    span.set_status(span.status.__class__.ERROR)  # type: ignore
                except Exception:
                    pass
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            if span:
                try:
                    span.set_attribute("http.status_code", getattr(response, "status_code", 0))
                    span.set_attribute("response_time_ms", elapsed_ms)
                    span.end()
                except Exception:
                    pass

        # ------------------------------------------------------------------
        # Inject trace headers into response
        # ------------------------------------------------------------------
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers[self.CORRELATION_HEADER] = corr_id
        response.headers[self.REQUEST_ID_HEADER] = req_id
        response.headers[self.RESPONSE_TIME_HEADER] = f"{elapsed_ms}ms"

        if self.propagate_b3:
            response.headers["X-B3-TraceId"] = corr_id
            response.headers["X-B3-SpanId"] = req_id[:16]

        logger.debug(
            "Request complete",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": elapsed_ms,
            },
        )

        return response


# ---------------------------------------------------------------------------
# Utility — inject correlation ID from background tasks
# ---------------------------------------------------------------------------

def set_background_trace(correlation_id: Optional[str] = None) -> str:
    """
    Call at the start of a background task to assign a trace context.
    Returns the correlation ID used.
    """
    cid = correlation_id or f"bg-{uuid.uuid4()}"
    correlation_id_var.set(cid)
    request_id_var.set(str(uuid.uuid4()))
    return cid

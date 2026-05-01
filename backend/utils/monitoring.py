"""
Monitoring and observability utilities
"""
import os
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.httpx import HttpxIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None
    FastApiIntegration = None
    LoggingIntegration = None
    HttpxIntegration = None
    SqlalchemyIntegration = None

from typing import Optional


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    enable_tracing: bool = True
):
    """
    Initialize Sentry for error tracking and APM
    
    Args:
        dsn: Sentry DSN (defaults to SENTRY_DSN_BACKEND env var)
        environment: Environment name (dev/staging/prod)
        release: Release version
        traces_sample_rate: Sample rate for performance traces (0.0 to 1.0)
        enable_tracing: Enable performance monitoring
    """
    if not SENTRY_AVAILABLE:
        # Sentry SDK not installed, skip initialization
        return
    
    dsn = dsn or os.getenv("SENTRY_DSN_BACKEND")
    if not dsn:
        # Sentry not configured, skip initialization
        return
    
    environment = environment or os.getenv("SENTRY_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
    release = release or os.getenv("SENTRY_RELEASE", "1.0.0")
    
    # Configure Sentry
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=traces_sample_rate if enable_tracing else 0.0,
        enable_tracing=enable_tracing,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(
                level=None,  # Capture all logs
                event_level=None  # Send all log levels as events
            ),
            HttpxIntegration(),
            SqlalchemyIntegration(),
        ],
        # Set sample rate for profiling
        profiles_sample_rate=0.1 if enable_tracing else 0.0,
        # Custom tags
        before_send=lambda event, hint: add_custom_tags(event),
        # Ignore certain errors
        ignore_errors=[
            KeyboardInterrupt,
            # Don't track rate limit errors
            "429",
        ],
    )
    
    # Set global tags
    sentry_sdk.set_tag("service", "AETHER-SCORE-backend")
    sentry_sdk.set_tag("version", release)


def add_custom_tags(event):
    """Add custom tags to Sentry events"""
    # Add service name
    event.setdefault("tags", {})["service"] = "AETHER-SCORE-backend"
    
    # Add additional context if available
    if "extra" not in event:
        event["extra"] = {}
    
    return event


def capture_exception(error: Exception, **kwargs):
    """Capture an exception in Sentry with additional context"""
    if not SENTRY_AVAILABLE:
        return
    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **kwargs):
    """Capture a message in Sentry with additional context"""
    if not SENTRY_AVAILABLE:
        return
    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        sentry_sdk.capture_message(message, level=level)


def set_user_context(address: Optional[str] = None, **kwargs):
    """Set user context for Sentry (privacy-compliant)"""
    # Only use anonymized/hashed address for privacy
    user_context = {}
    
    if address:
        # Hash address for privacy (first 8 chars + last 4 chars)
        if len(address) >= 12:
            anonymized = f"{address[:8]}...{address[-4:]}"
        else:
            anonymized = "***"
        user_context["id"] = anonymized
    
    # Add any additional context
    user_context.update(kwargs)
    
    if SENTRY_AVAILABLE:
        sentry_sdk.set_user(user_context)


def add_breadcrumb(message: str, category: str = "default", level: str = "info", **kwargs):
    """Add a breadcrumb to Sentry"""
    if not SENTRY_AVAILABLE:
        return
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=kwargs
    )



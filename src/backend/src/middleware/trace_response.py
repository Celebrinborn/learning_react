"""Middleware to add trace_id to response headers"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace


class TraceResponseMiddleware(BaseHTTPMiddleware):
    """Add X-Trace-ID header to all responses"""

    async def dispatch(self, request: Request, call_next):
        """
        Process request and add trace_id to response headers.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response with X-Trace-ID header added
        """
        response = await call_next(request)

        # Extract trace_id from current OpenTelemetry span
        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context.is_valid:
            # Format as 32 hex characters
            trace_id = format(span_context.trace_id, '032x')
            response.headers["X-Trace-ID"] = trace_id

        return response

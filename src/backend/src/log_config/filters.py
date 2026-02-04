"""Logging filters for adding context to log records"""
import logging
from opentelemetry import trace


class TraceContextFilter(logging.Filter):
    """Adds trace_id and span_id from OpenTelemetry to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add trace context to log record.

        Args:
            record: The log record to enrich

        Returns:
            True to allow the record to be logged
        """
        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context.is_valid:
            # Format as 32 hex characters for trace_id, 16 for span_id
            record.trace_id = format(span_context.trace_id, '032x')
            record.span_id = format(span_context.span_id, '016x')
        else:
            # No active span - set to None
            record.trace_id = None
            record.span_id = None

        return True

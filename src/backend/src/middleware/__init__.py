"""Middleware for DND Backend"""

from .trace_response import TraceResponseMiddleware

__all__ = ["TraceResponseMiddleware"]

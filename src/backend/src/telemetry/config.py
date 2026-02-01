"""
OpenTelemetry configuration for distributed tracing.
Configures OTLP exporter to localhost:4317 (no-op until collector is running).
"""
import os
from typing import Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore[import-untyped]


_tracer: trace.Tracer | None = None


def setup_telemetry(service_name: str = "dnd-backend") -> None:
    """
    Initialize OpenTelemetry tracer provider and instrumentation.
    
    Configures OTLP exporter to send traces to localhost:4317.
    Will silently fail (no-op) if no collector is running.
    
    Args:
        service_name: Name of the service for trace identification
    """
    global _tracer
    
    # Get version from environment or default
    version = os.getenv("SERVICE_VERSION", "0.1.0")
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Create resource with service metadata
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: version,
        "deployment.environment": environment,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter (no-op until receiver is running)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # Use insecure for localhost development
    )
    
    # Add batch span processor for async export
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    
    # Initialize tracer
    _tracer = trace.get_tracer(__name__)
    
    # FastAPI auto-instrumentation will be done after app creation
    

def instrument_fastapi(app: Any) -> None:
    """
    Instrument FastAPI application with OpenTelemetry.
    Call this after FastAPI app is created.
    
    Args:
        app: FastAPI application instance
    """
    FastAPIInstrumentor.instrument_app(app)


def get_tracer() -> trace.Tracer:
    """
    Get the application tracer instance.
    
    Returns a no-op tracer if telemetry hasn't been initialized,
    allowing code to work in test environments without setup.
    
    Returns:
        OpenTelemetry tracer for creating manual spans
    """
    if _tracer is None:
        # Return a no-op tracer for test environments
        return trace.get_tracer(__name__)
    return _tracer

"""
OpenTelemetry configuration for distributed tracing.
Configures OTLP exporter to localhost:4317 (no-op until collector is running).
"""
import os
import logging
from typing import Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore[import-untyped]


logger = logging.getLogger(__name__)
_tracer: trace.Tracer | None = None
_telemetry_enabled: bool = False


def setup_telemetry(service_name: str = "dnd-backend") -> None:
    """
    Initialize OpenTelemetry tracer provider and instrumentation.
    
    Configures OTLP exporter to send traces to localhost:4317.
    Will skip setup entirely if TELEMETRY_ENABLED is false.
    
    Args:
        service_name: Name of the service for trace identification
    """
    global _tracer, _telemetry_enabled
    
    # Check if telemetry is enabled
    telemetry_enabled_str = os.getenv("TELEMETRY_ENABLED", "false").lower()
    _telemetry_enabled = telemetry_enabled_str in ("true", "1", "yes")
    
    if not _telemetry_enabled:
        logger.info("Telemetry disabled via TELEMETRY_ENABLED=false")
        return
    
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
    
    logger.info(f"Telemetry initialized for {service_name} v{version} ({environment})")
    # FastAPI auto-instrumentation will be done after app creation
    

def instrument_fastapi(app: Any) -> None:
    """
    Instrument FastAPI application with OpenTelemetry.
    Call this after FastAPI app is created.
    Skips instrumentation if telemetry is disabled.
    
    Args:
        app: FastAPI application instance
    """
    if not _telemetry_enabled:
        return
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

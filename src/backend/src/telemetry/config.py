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


def _is_truthy_env(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() in ("true", "1", "yes")


def setup_telemetry(service_name: str = "dnd-backend") -> None:
    """
    Initialize OpenTelemetry tracer provider and instrumentation.

    Contract changes vs old behavior:
    - We still read TELEMETRY_ENABLED and expose it via _telemetry_enabled.
    - Even when TELEMETRY_ENABLED=false, we STILL initialize tracing context so
      trace/span IDs exist for correlation (export is skipped).
    - If TELEMETRY_ENABLED=true, we configure the OTLP exporter.

    Args:
        service_name: Name of the service for trace identification
    """
    global _tracer, _telemetry_enabled

    # Keep the existing "enabled" contract/flag
    _telemetry_enabled = _is_truthy_env("TELEMETRY_ENABLED", "false")

    # Get version from environment or default
    version = os.getenv("SERVICE_VERSION", "0.1.0")
    environment = os.getenv("ENVIRONMENT", "development")

    # Create resource with service metadata
    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: version,
            "deployment.environment": environment,
        }
    )

    # Create tracer provider (ALWAYS, so we always have non-empty trace/span IDs)
    provider = TracerProvider(resource=resource)

    # Only attach an exporter when enabled; otherwise it's purely local context.
    if _telemetry_enabled:
        # For the OTLP *gRPC* exporter, prefer "host:port" (no scheme).
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

        # "insecure" just means "no TLS" for the gRPC channel.
        # Default behavior:
        # - If endpoint is localhost/127.0.0.1, allow insecure (dev default).
        # - If endpoint is not local, require explicit opt-in via OTEL_EXPORTER_OTLP_INSECURE=true.
        host = otlp_endpoint.split(":")[0]
        is_local = host in ("localhost", "127.0.0.1")

        insecure = is_local or _is_truthy_env("OTEL_EXPORTER_OTLP_INSECURE", "false")
        if not insecure and not is_local:
            logger.warning(
                "Telemetry export enabled but OTLP endpoint is non-local and insecure export is not allowed. "
                "Set OTEL_EXPORTER_OTLP_INSECURE=true if you truly want plaintext, or configure TLS."
            )
        else:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                insecure=True,  # plaintext gRPC (dev/local)
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    else:
        logger.info("Telemetry export disabled via TELEMETRY_ENABLED=false (context still initialized)")

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

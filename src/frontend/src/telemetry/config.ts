/**
 * OpenTelemetry configuration for DND Frontend.
 * Configures OTLP HTTP exporter to localhost:4318 (no-op until collector is running).
 */
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { trace, Tracer } from '@opentelemetry/api';

let tracer: Tracer | null = null;

/**
 * Initialize OpenTelemetry tracer provider and instrumentation.
 * Configures OTLP exporter to send traces to localhost:4318.
 * Will silently fail (no-op) if no collector is running.
 */
export function setupTelemetry(serviceName: string = 'dnd-frontend'): void {
  // Get version and environment from environment variables
  const version = import.meta.env.VITE_SERVICE_VERSION || '0.0.0';
  const environment = import.meta.env.VITE_ENVIRONMENT || 'development';

  // Create resource with service metadata
  const resource = new Resource({
    [ATTR_SERVICE_NAME]: serviceName,
    [ATTR_SERVICE_VERSION]: version,
    'deployment.environment': environment,
  });

  // Create tracer provider
  const provider = new WebTracerProvider({
    resource,
  });

  // Configure OTLP HTTP exporter (no-op until receiver is running)
  const otlpEndpoint = import.meta.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces';
  const otlpExporter = new OTLPTraceExporter({
    url: otlpEndpoint,
  });

  // Add batch span processor for async export
  provider.addSpanProcessor(new BatchSpanProcessor(otlpExporter));

  // Register the provider globally
  provider.register();

  // Initialize tracer
  tracer = trace.getTracer(serviceName, version);

  // Auto-instrument fetch API
  registerInstrumentations({
    instrumentations: [
      new FetchInstrumentation({
        propagateTraceHeaderCorsUrls: [
          /localhost:8000/,  // Backend API
          new RegExp(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'),
        ],
        clearTimingResources: true,
        applyCustomAttributesOnSpan: (span: any, request: any, response: any) => {
          if (response instanceof Response) {
            span.setAttribute('http.status_code', response.status);
            span.setAttribute('http.status_text', response.statusText);
          }
          if (request instanceof Request) {
            span.setAttribute('http.url', request.url);
            span.setAttribute('http.method', request.method);
          }
        },
      }),
    ],
  });
}

/**
 * Get the application tracer instance.
 * @returns OpenTelemetry tracer for creating manual spans
 * @throws Error if telemetry hasn't been initialized
 */
export function getTracer(): Tracer {
  if (!tracer) {
    throw new Error('Telemetry not initialized. Call setupTelemetry() first.');
  }
  return tracer;
}

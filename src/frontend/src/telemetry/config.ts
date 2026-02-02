/**
 * OpenTelemetry configuration for DND Frontend.
 * Configures OTLP HTTP exporter to localhost:4318 (no-op until collector is running).
 */
import { trace, type Tracer } from '@opentelemetry/api';

let tracer: Tracer | null = null;
let initialized = false;

/**
 * Check if telemetry is enabled via environment variable.
 */
function isTelemetryEnabled(): boolean {
  const enabled = import.meta.env.VITE_TELEMETRY_ENABLED;
  return enabled === 'true' || enabled === '1' || enabled === 'yes';
}

/**
 * Initialize OpenTelemetry tracer provider and instrumentation.
 * Configures OTLP exporter to send traces to localhost:4318.
 * Skips setup entirely if VITE_TELEMETRY_ENABLED is false.
 */
export async function setupTelemetry(serviceName: string = 'dnd-frontend'): Promise<void> {
  if (initialized) return;
  initialized = true;

  if (!isTelemetryEnabled()) {
    console.log('Telemetry disabled via VITE_TELEMETRY_ENABLED=false');
    return;
  }

  try {
    // Dynamic imports to avoid blocking initial page load
    const [
      { WebTracerProvider, BatchSpanProcessor },
      { OTLPTraceExporter },
      { Resource },
      { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION },
      { FetchInstrumentation },
      { registerInstrumentations },
    ] = await Promise.all([
      import('@opentelemetry/sdk-trace-web'),
      import('@opentelemetry/exporter-trace-otlp-http'),
      import('@opentelemetry/resources'),
      import('@opentelemetry/semantic-conventions'),
      import('@opentelemetry/instrumentation-fetch'),
      import('@opentelemetry/instrumentation'),
    ]);

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
          ],
          clearTimingResources: true,
        }),
      ],
    });

    console.log('OpenTelemetry initialized successfully');
  } catch (error) {
    console.warn('Failed to initialize OpenTelemetry:', error);
    // Continue without telemetry - app should still work
  }
}

/**
 * Get the application tracer instance.
 * Returns a no-op tracer if telemetry hasn't been initialized.
 * @returns OpenTelemetry tracer for creating manual spans
 */
export function getTracer(): Tracer {
  if (!tracer) {
    // Return a no-op tracer - won't throw, just does nothing
    return trace.getTracer('noop');
  }
  return tracer;
}

/**
 * OpenTelemetry configuration for DND Frontend.
 * Configures OTLP HTTP exporter to localhost:4318 (no-op until collector is running).
 */
import { trace, type Tracer } from '@opentelemetry/api';

let tracer: Tracer | null = null;
let initialized = false;

/**
 * Check if telemetry export is enabled via environment variable.
 * (Context/tracer setup should still happen even when disabled so correlation IDs don't go blank.)
 */
function isTelemetryEnabled(): boolean {
  const enabled = import.meta.env.VITE_TELEMETRY_ENABLED;
  return enabled === 'true' || enabled === '1' || enabled === 'yes';
}

/**
 * Initialize OpenTelemetry tracer provider and instrumentation.
 *
 * Contract changes vs old behavior:
 * - We still read VITE_TELEMETRY_ENABLED and honor it for EXPORT.
 * - Even when VITE_TELEMETRY_ENABLED=false, we STILL register a tracer provider
 *   so trace/span IDs exist for correlation (no exporter + no auto-instrumentation).
 */
export async function setupTelemetry(serviceName: string = 'dnd-frontend'): Promise<void> {
  if (initialized) return;
  initialized = true;

  const exportEnabled = isTelemetryEnabled();

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

    // Create tracer provider (ALWAYS, so IDs exist even if export is off)
    const provider = new WebTracerProvider({ resource });

    if (exportEnabled) {
      // Configure OTLP HTTP exporter (best-effort; collector may be down)
      const otlpEndpoint =
        import.meta.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces';

      // Enforce "no plaintext to non-local endpoints unless explicitly opted-in"
      // (Browser OTLP is always HTTP(S); this is about allowing http:// to non-local hosts.)
      let allowInsecureRemote = false;
      const allow = import.meta.env.VITE_OTEL_EXPORTER_OTLP_ALLOW_INSECURE_REMOTE;
      if (allow === 'true' || allow === '1' || allow === 'yes') allowInsecureRemote = true;

      let url: URL | null = null;
      try {
        url = new URL(otlpEndpoint);
      } catch {
        // If it's not a valid URL, OTLP exporter will throw; keep behavior in try/catch.
      }

      const isLocalHost =
        !!url && (url.hostname === 'localhost' || url.hostname === '127.0.0.1');

      const isHttp = !!url && url.protocol === 'http:';
      const isRemote = !!url && !isLocalHost;

      if (url && isHttp && isRemote && !allowInsecureRemote) {
        console.warn(
          'Telemetry export enabled, but refusing to send traces over plain HTTP to a non-local endpoint. ' +
            'Use https://..., localhost, or set VITE_OTEL_EXPORTER_OTLP_ALLOW_INSECURE_REMOTE=true to override.'
        );
      } else {
        const otlpExporter = new OTLPTraceExporter({ url: otlpEndpoint });
        provider.addSpanProcessor(new BatchSpanProcessor(otlpExporter));

        // Auto-instrument fetch ONLY when export is enabled
        registerInstrumentations({
          instrumentations: [
            new FetchInstrumentation({
              propagateTraceHeaderCorsUrls: [
                /localhost:8000/, // Backend API
              ],
              clearTimingResources: true,
            }),
          ],
        });
      }
    } else {
      console.log('Telemetry export disabled via VITE_TELEMETRY_ENABLED=false (context still initialized)');
    }

    // Register the provider globally (ALWAYS)
    provider.register();

    // Initialize tracer (ALWAYS)
    tracer = trace.getTracer(serviceName, version);

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

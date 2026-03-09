import { useEffect, useState } from 'react';
import { buildApiUrl } from '../config/service.config';

const POLL_INTERVAL_MS = 30_000;

export function useBackendHealth(): { isHealthy: boolean } {
  const [isHealthy, setIsHealthy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    async function check(): Promise<void> {
      try {
        const res = await fetch(buildApiUrl('/health'));
        if (!cancelled && res.ok) {
          setIsHealthy(true);
          return;
        }
      } catch {
        // network error — backend not up yet
      }

      if (!cancelled) {
        timeoutId = setTimeout(check, POLL_INTERVAL_MS);
      }
    }

    void check();

    return () => {
      cancelled = true;
      if (timeoutId !== null) {
        clearTimeout(timeoutId);
      }
    };
  }, []);

  return { isHealthy };
}

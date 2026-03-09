/**
 * Tests for useBackendHealth hook
 * Testing behavior: Polls /health endpoint and reports backend status
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

vi.mock('../config/service.config', () => ({
  buildApiUrl: (path: string) => `http://localhost:8000${path}`,
}));

import { useBackendHealth } from '../hooks/useBackendHealth';

// Flush pending microtasks (lets resolved promises run)
const flushMicrotasks = () => act(async () => { await Promise.resolve(); });

describe('useBackendHealth', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('returns isHealthy: false initially before fetch resolves', () => {
    // fetch never resolves during this test
    vi.mocked(fetch).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useBackendHealth());

    expect(result.current.isHealthy).toBe(false);
  });

  it('transitions to isHealthy: true when fetch returns 200', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 200 }));

    const { result } = renderHook(() => useBackendHealth());
    await flushMicrotasks();

    expect(result.current.isHealthy).toBe(true);
  });

  it('stays isHealthy: false when fetch returns non-200', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 503 }));

    const { result } = renderHook(() => useBackendHealth());
    await flushMicrotasks();

    expect(result.current.isHealthy).toBe(false);
  });

  it('stays isHealthy: false when fetch throws a network error', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useBackendHealth());
    await flushMicrotasks();

    expect(result.current.isHealthy).toBe(false);
  });

  it('retries after 30 seconds on failure then becomes healthy', async () => {
    vi.mocked(fetch)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValue(new Response(null, { status: 200 }));

    const { result } = renderHook(() => useBackendHealth());

    // First attempt fails
    await flushMicrotasks();
    expect(result.current.isHealthy).toBe(false);

    // Advance 30s to trigger retry, then flush the retry's promise
    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });

    expect(result.current.isHealthy).toBe(true);
  });

  it('stops polling after backend comes up', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response(null, { status: 200 }));

    renderHook(() => useBackendHealth());
    await flushMicrotasks();

    expect(fetch).toHaveBeenCalledTimes(1);

    // Advance well past the interval — no additional calls
    await act(async () => {
      await vi.advanceTimersByTimeAsync(90_000);
    });

    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it('does not update state after unmount', async () => {
    let resolveFetch!: (value: Response) => void;
    vi.mocked(fetch).mockReturnValue(
      new Promise<Response>((resolve) => { resolveFetch = resolve; })
    );

    const { unmount } = renderHook(() => useBackendHealth());
    unmount();

    // Resolve after unmount — should not throw
    await act(async () => {
      resolveFetch(new Response(null, { status: 200 }));
      await Promise.resolve();
    });
  });
});

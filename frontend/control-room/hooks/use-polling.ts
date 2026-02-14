'use client';

/**
 * Generic Polling Hook
 * Provides a reusable polling mechanism for any async operation
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface UsePollingOptions<T> {
  /** Function to call on each poll */
  fetchFn: () => Promise<T>;
  /** Polling interval in milliseconds */
  interval: number;
  /** Whether polling is enabled */
  enabled?: boolean;
  /** Callback called on successful fetch */
  onSuccess?: (data: T) => void;
  /** Callback called on error */
  onError?: (error: Error) => void;
  /** Whether to fetch immediately on mount */
  immediate?: boolean;
}

export interface UsePollingReturn<T> {
  /** Latest data from fetchFn */
  data: T | null;
  /** Whether a fetch is currently in progress */
  isLoading: boolean;
  /** Error from last fetch attempt */
  error: Error | null;
  /** Manually trigger a refetch */
  refetch: () => Promise<void>;
  /** Whether polling is currently active */
  isPolling: boolean;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Generic polling hook with proper cleanup and error handling
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = usePolling({
 *   fetchFn: () => api.getContainers(),
 *   interval: 10000,
 *   enabled: true,
 *   onSuccess: (data) => console.log('Fetched', data),
 * });
 * ```
 */
export function usePolling<T>(
  options: UsePollingOptions<T>
): UsePollingReturn<T> {
  const {
    fetchFn,
    interval,
    enabled = true,
    onSuccess,
    onError,
    immediate = true,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(immediate);
  const [error, setError] = useState<Error | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(enabled);

  // Use refs for callbacks to avoid recreating interval
  const fetchFnRef = useRef(fetchFn);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  // Keep refs in sync with latest callbacks
  useEffect(() => {
    fetchFnRef.current = fetchFn;
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  }, [fetchFn, onSuccess, onError]);

  // Track enabled state
  useEffect(() => {
    setIsPolling(enabled);
  }, [enabled]);

  const fetch = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await fetchFnRef.current();
      setData(result);
      onSuccessRef.current?.(result);
    } catch (err) {
      const errorObj =
        err instanceof Error ? err : new Error(String(err));
      setError(errorObj);
      onErrorRef.current?.(errorObj);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refetch = useCallback(async () => {
    await fetch();
  }, [fetch]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Immediate fetch if enabled
    if (immediate) {
      fetch();
    }

    // Set up polling interval
    const intervalId = setInterval(() => {
      fetch();
    }, interval);

    // Cleanup
    return () => {
      clearInterval(intervalId);
    };
  }, [enabled, interval, immediate, fetch]);

  return {
    data,
    isLoading,
    error,
    refetch,
    isPolling,
  };
}

// ============================================================================
// Utility Hook: Polling with Status Tracking
// ============================================================================

export interface UsePollingWithStatusOptions<T> extends UsePollingOptions<T> {
  /** Initial data to use before first fetch completes */
  initialData?: T | null;
}

export interface UsePollingWithStatusReturn<T> extends UsePollingReturn<T> {
  /** Timestamp of last successful fetch */
  lastFetchedAt: Date | null;
  /** Timestamp of last error */
  lastErrorAt: Date | null;
}

/**
 * Extended polling hook with status timestamps
 */
export function usePollingWithStatus<T>(
  options: UsePollingWithStatusOptions<T>
): UsePollingWithStatusReturn<T> {
  const { initialData = null, ...pollingOptions } = options;

  const baseResult = usePolling<T>(pollingOptions);

  const [lastFetchedAt, setLastFetchedAt] = useState<Date | null>(null);
  const [lastErrorAt, setLastErrorAt] = useState<Date | null>(null);

  // Track timestamps
  useEffect(() => {
    if (baseResult.data && !baseResult.error) {
      setLastFetchedAt(new Date());
    }
    if (baseResult.error) {
      setLastErrorAt(new Date());
    }
  }, [baseResult.data, baseResult.error]);

  return {
    ...baseResult,
    data: baseResult.data ?? initialData,
    lastFetchedAt,
    lastErrorAt,
  };
}

export default usePolling;

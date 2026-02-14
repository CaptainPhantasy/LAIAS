'use client';

/**
 * useMetrics Hook
 * Hook for fetching and tracking container metrics with history
 */

import { useState, useCallback, useEffect, useRef } from 'react';

import type { MetricsResponse, MetricDataPoint, ContainerMetricsHistory } from '../types';
import { getContainerMetrics } from '../lib/api';
import { POLLING_INTERVALS, METRICS_CHART } from '../lib/constants';

// ============================================================================
// Types
// ============================================================================

export interface UseMetricsOptions {
  /** Container ID to fetch metrics for */
  containerId: string | null;
  /** Enable automatic refresh */
  autoRefresh?: boolean;
  /** Custom refresh interval in milliseconds */
  refreshInterval?: number;
}

export interface UseMetricsReturn {
  /** Current metrics snapshot */
  metrics: MetricsResponse | null;
  /** Historical metrics for charts */
  history: ContainerMetricsHistory | null;
  /** Whether currently fetching */
  isLoading: boolean;
  /** Error message if fetch failed */
  error: string | null;
  /** Manually trigger a refetch */
  refetch: () => Promise<void>;
  /** Clear all history */
  clearHistory: () => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Create a metric data point with current timestamp
 */
function createDataPoint(value: number): MetricDataPoint {
  return {
    timestamp: new Date().toISOString(),
    value,
  };
}

/**
 * Trim history array to max size
 */
function trimHistory<T>(array: T[], maxSize: number): T[] {
  if (array.length <= maxSize) {
    return array;
  }
  return array.slice(-maxSize);
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for container metrics with history tracking
 *
 * @example
 * ```tsx
 * const { metrics, history, isLoading, error } = useMetrics({
 *   containerId: 'abc123',
 *   autoRefresh: true,
 *   refreshInterval: 5000,
 * });
 * ```
 */
export function useMetrics(
  options: UseMetricsOptions
): UseMetricsReturn {
  const {
    containerId,
    autoRefresh = false,
    refreshInterval = POLLING_INTERVALS.METRICS,
  } = options;

  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [history, setHistory] = useState<ContainerMetricsHistory | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const maxHistoryPoints = METRICS_CHART.MAX_DATA_POINTS;

  // Track mounted state
  const isMountedRef = useRef(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetch = useCallback(async () => {
    if (!containerId || !isMountedRef.current) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const result = await getContainerMetrics(containerId);

      if (!isMountedRef.current) return;

      setMetrics(result);

       // Update history
       setHistory((prev) => {
         const newCpuPoint = createDataPoint(result.cpu?.percent ?? 0);
         const newMemoryPoint = createDataPoint(result.memory?.percent ?? 0);
         const newRxPoint = createDataPoint(result.network?.rx_bytes ?? 0);
         const newTxPoint = createDataPoint(result.network?.tx_bytes ?? 0);

        // Initialize or append to history
        const cpuHistory = prev
          ? trimHistory([...prev.cpu, newCpuPoint], maxHistoryPoints)
          : [newCpuPoint];
        const memoryHistory = prev
          ? trimHistory([...prev.memory, newMemoryPoint], maxHistoryPoints)
          : [newMemoryPoint];
        const rxHistory = prev
          ? trimHistory([...prev.network.rx, newRxPoint], maxHistoryPoints)
          : [newRxPoint];
        const txHistory = prev
          ? trimHistory([...prev.network.tx, newTxPoint], maxHistoryPoints)
          : [newTxPoint];

        return {
          containerId,
          cpu: cpuHistory,
          memory: memoryHistory,
          network: {
            rx: rxHistory,
            tx: txHistory,
          },
        };
      });
    } catch (err) {
      if (!isMountedRef.current) return;

      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch metrics';
      setError(errorMessage);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [containerId, maxHistoryPoints]);

  const refetch = useCallback(async () => {
    await fetch();
  }, [fetch]);

  const clearHistory = useCallback(() => {
    setHistory(null);
  }, []);

  // Set up polling
  useEffect(() => {
    if (!containerId) {
      setMetrics(null);
      setHistory(null);
      return;
    }

    // Initial fetch
    fetch();

    // Set up polling interval
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        fetch();
      }, refreshInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [containerId, autoRefresh, refreshInterval, fetch]);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return {
    metrics,
    history,
    isLoading,
    error,
    refetch,
    clearHistory,
  };
}

export default useMetrics;

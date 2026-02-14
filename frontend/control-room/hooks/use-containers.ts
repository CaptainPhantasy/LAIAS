'use client';

/**
 * useContainers Hook
 * Hook for fetching and managing container list with optional auto-refresh
 */

import { useState, useCallback, useEffect, useRef } from 'react';

import type { ContainerInfo, ContainerListResponse, ContainerStatus } from '../types';
import { listContainers } from '../lib/api';
import { POLLING_INTERVALS } from '../lib/constants';

// ============================================================================
// Types
// ============================================================================

export interface UseContainersOptions {
  /** Enable automatic polling refresh */
  autoRefresh?: boolean;
  /** Custom refresh interval in milliseconds */
  refreshInterval?: number;
  /** Filter by container status */
  status?: ContainerStatus | 'all';
  /** Include stopped containers */
  all?: boolean;
  /** Filter by agent ID */
  agentId?: string;
}

export interface UseContainersReturn {
  /** List of containers */
  containers: ContainerInfo[];
  /** Total count of containers */
  total: number;
  /** Whether currently fetching (initial load) */
  isLoading: boolean;
  /** Whether currently refetching (background refresh) */
  isRefetching: boolean;
  /** Error message if fetch failed */
  error: string | null;
  /** Manually trigger a refetch */
  refetch: () => Promise<void>;
  /** Whether auto-refresh is active */
  isPolling: boolean;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for container list with auto-refresh capability
 *
 * @example
 * ```tsx
 * const { containers, isLoading, error, refetch } = useContainers({
 *   autoRefresh: true,
 *   status: 'running',
 * });
 * ```
 */
export function useContainers(
  options: UseContainersOptions = {}
): UseContainersReturn {
  const {
    autoRefresh = false,
    refreshInterval = POLLING_INTERVALS.CONTAINERS,
    status,
    all,
    agentId,
  } = options;

  const [containers, setContainers] = useState<ContainerInfo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(autoRefresh);
  const [isRefetching, setIsRefetching] = useState<boolean>(false);

  // Track options to detect changes
  const optionsRef = useRef({ status, all, agentId, autoRefresh, refreshInterval });
  const currentParams = { status, all, agentId };

  // Check if params changed
  const paramsChanged =
    optionsRef.current.status !== status ||
    optionsRef.current.all !== all ||
    optionsRef.current.agentId !== agentId;

  // Update ref when options change
  useEffect(() => {
    optionsRef.current = { status, all, agentId, autoRefresh, refreshInterval };
  }, [status, all, agentId, autoRefresh, refreshInterval]);

  const fetch = useCallback(async () => {
    try {
      // Only show full loading on initial fetch, use refetching for subsequent
      const isInitialFetch = containers.length === 0;
      if (isInitialFetch) {
        setIsLoading(true);
      } else {
        setIsRefetching(true);
      }
      setError(null);

      const params: Parameters<typeof listContainers>[0] = {};

      if (status !== undefined) {
        params.status = status;
      }
      if (all !== undefined) {
        params.all = all;
      }
      if (agentId !== undefined) {
        params.agent_id = agentId;
      }

      const result: ContainerListResponse = await listContainers(params);

      // Handle different response shapes
      const containerList = Array.isArray(result)
        ? result
        : (result as { containers?: ContainerInfo[] })?.containers ?? [];

      setContainers(containerList);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch containers';
      setError(errorMessage);
      setContainers([]);
    } finally {
      setIsLoading(false);
      setIsRefetching(false);
    }
  }, [status, all, agentId, containers.length]);

  // Refetch function for manual refresh
  const refetch = useCallback(async () => {
    await fetch();
  }, [fetch]);

  // Initial fetch and polling setup
  useEffect(() => {
    // Fetch immediately
    fetch();

    // Set up polling if enabled
    if (!autoRefresh) {
      return;
    }

    const intervalId = setInterval(() => {
      fetch();
    }, refreshInterval);

    setIsPolling(true);

    return () => {
      clearInterval(intervalId);
      setIsPolling(false);
    };
  }, [autoRefresh, refreshInterval]);

  // Refetch when filter params change
  useEffect(() => {
    if (paramsChanged) {
      fetch();
    }
  }, [paramsChanged, fetch]);

  const total = containers.length;

  return {
    containers,
    total,
    isLoading,
    isRefetching,
    error,
    refetch,
    isPolling,
  };
}

// ============================================================================
// Utility Hook: Container Counts by Status
// ============================================================================

export interface UseContainerCountsReturn {
  /** Count of running containers */
  running: number;
  /** Count of stopped containers */
  stopped: number;
  /** Count of paused containers */
  paused: number;
  /** Total count */
  total: number;
  /** Whether currently fetching */
  isLoading: boolean;
  /** Error message if fetch failed */
  error: string | null;
}

/**
 * Hook for getting container counts by status
 */
export function useContainerCounts(
  options?: Omit<UseContainersOptions, 'status'>
): UseContainerCountsReturn {
  const { containers, isLoading, error } = useContainers({
    ...options,
    all: true,
  });

  const counts = containers.reduce(
    (acc, container) => {
      const status = container.status || 'stopped';
      acc[status as keyof typeof acc] = (acc[status as keyof typeof acc] ?? 0) + 1;
      return acc;
    },
    { running: 0, stopped: 0, paused: 0, exited: 0 as number, error: 0 as number }
  );

  return {
    running: counts.running,
    stopped: counts.stopped + (counts.exited ?? 0),
    paused: counts.paused,
    total: containers.length,
    isLoading,
    error,
  };
}

export default useContainers;

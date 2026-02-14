'use client';

/**
 * useContainerActions Hook
 * Hook for executing container actions with loading and error states
 */

import { useState, useCallback, useRef } from 'react';

import type { ActionResponse } from '../types';
import {
  startContainer,
  stopContainer,
  restartContainer,
  removeContainer,
} from '../lib/api';

// ============================================================================
// Types
// ============================================================================

export interface UseContainerActionsReturn {
  /** Start a container */
  start: (id: string) => Promise<ActionResponse>;
  /** Stop a container */
  stop: (id: string) => Promise<ActionResponse>;
  /** Restart a container */
  restart: (id: string) => Promise<ActionResponse>;
  /** Remove a container */
  remove: (id: string) => Promise<void>;
  /** Per-container loading state */
  loading: Record<string, boolean>;
  /** Per-container error state */
  errors: Record<string, string | null>;
  /** Clear error for a specific container */
  clearError: (id: string) => void;
  /** Clear all errors */
  clearAllErrors: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for container actions with individual loading/error tracking
 *
 * @example
 * ```tsx
 * const { start, stop, restart, remove, loading, errors } = useContainerActions();
 *
 * const handleStart = async (id: string) => {
 *   const result = await start(id);
 *   if (result.success) {
 *     toast.success('Container started');
 *   }
 * };
 * ```
 */
export function useContainerActions(): UseContainerActionsReturn {
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});

  // Track pending actions to prevent duplicate calls
  const pendingActions = useRef<Set<string>>(new Set());

  const setContainerLoading = useCallback((id: string, isLoading: boolean) => {
    setLoading((prev) => ({ ...prev, [id]: isLoading }));
  }, []);

  const setContainerError = useCallback((id: string, error: string | null) => {
    setErrors((prev) => ({ ...prev, [id]: error }));
  }, []);

  const start = useCallback(async (id: string): Promise<ActionResponse> => {
    // Prevent duplicate calls
    if (pendingActions.current.has(`${id}:start`)) {
      return { success: false, message: 'Action already in progress' };
    }

    try {
      pendingActions.current.add(`${id}:start`);
      setContainerLoading(id, true);
      setContainerError(id, null);

      const result = await startContainer(id);

      if (!result.success) {
        setContainerError(id, result.message || 'Failed to start container');
      }

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start container';
      setContainerError(id, errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setContainerLoading(id, false);
      pendingActions.current.delete(`${id}:start`);
    }
  }, [setContainerLoading, setContainerError]);

  const stop = useCallback(async (id: string): Promise<ActionResponse> => {
    if (pendingActions.current.has(`${id}:stop`)) {
      return { success: false, message: 'Action already in progress' };
    }

    try {
      pendingActions.current.add(`${id}:stop`);
      setContainerLoading(id, true);
      setContainerError(id, null);

      const result = await stopContainer(id);

      if (!result.success) {
        setContainerError(id, result.message || 'Failed to stop container');
      }

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to stop container';
      setContainerError(id, errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setContainerLoading(id, false);
      pendingActions.current.delete(`${id}:stop`);
    }
  }, [setContainerLoading, setContainerError]);

  const restart = useCallback(async (id: string): Promise<ActionResponse> => {
    if (pendingActions.current.has(`${id}:restart`)) {
      return { success: false, message: 'Action already in progress' };
    }

    try {
      pendingActions.current.add(`${id}:restart`);
      setContainerLoading(id, true);
      setContainerError(id, null);

      const result = await restartContainer(id);

      if (!result.success) {
        setContainerError(id, result.message || 'Failed to restart container');
      }

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restart container';
      setContainerError(id, errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setContainerLoading(id, false);
      pendingActions.current.delete(`${id}:restart`);
    }
  }, [setContainerLoading, setContainerError]);

  const remove = useCallback(async (id: string): Promise<void> => {
    if (pendingActions.current.has(`${id}:remove`)) {
      throw new Error('Action already in progress');
    }

    try {
      pendingActions.current.add(`${id}:remove`);
      setContainerLoading(id, true);
      setContainerError(id, null);

      await removeContainer(id);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to remove container';
      setContainerError(id, errorMessage);
      throw err;
    } finally {
      setContainerLoading(id, false);
      pendingActions.current.delete(`${id}:remove`);
    }
  }, [setContainerLoading, setContainerError]);

  const clearError = useCallback((id: string) => {
    setContainerError(id, null);
  }, [setContainerError]);

  const clearAllErrors = useCallback(() => {
    setErrors({});
  }, []);

  return {
    start,
    stop,
    restart,
    remove,
    loading,
    errors,
    clearError,
    clearAllErrors,
  };
}

// ============================================================================
// Utility Hook: Single Container Actions
// ============================================================================

export interface UseSingleContainerActionsOptions {
  /** Container ID to perform actions on */
  containerId: string;
}

export interface UseSingleContainerActionsReturn {
  /** Start the container */
  start: () => Promise<ActionResponse>;
  /** Stop the container */
  stop: () => Promise<ActionResponse>;
  /** Restart the container */
  restart: () => Promise<ActionResponse>;
  /** Remove the container */
  remove: () => Promise<void>;
  /** Whether any action is in progress */
  isLoading: boolean;
  /** Error from last action */
  error: string | null;
  /** Clear the error */
  clearError: () => void;
}

/**
 * Hook for actions on a single container
 */
export function useSingleContainerActions(
  options: UseSingleContainerActionsOptions
): UseSingleContainerActionsReturn {
  const { containerId } = options;

  const actions = useContainerActions();

  const start = useCallback(async () => {
    return actions.start(containerId);
  }, [actions, containerId]);

  const stop = useCallback(async () => {
    return actions.stop(containerId);
  }, [actions, containerId]);

  const restart = useCallback(async () => {
    return actions.restart(containerId);
  }, [actions, containerId]);

  const remove = useCallback(async () => {
    return actions.remove(containerId);
  }, [actions, containerId]);

  const clearError = useCallback(() => {
    actions.clearError(containerId);
  }, [actions]);

  const isLoading = actions.loading[containerId] ?? false;
  const error = actions.errors[containerId] ?? null;

  return {
    start,
    stop,
    restart,
    remove,
    isLoading,
    error,
    clearError,
  };
}

export default useContainerActions;

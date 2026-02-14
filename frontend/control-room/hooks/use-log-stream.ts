'use client';

/**
 * useLogStream Hook
 * Hook for streaming container logs via Server-Sent Events
 */

import { useState, useCallback, useEffect, useRef } from 'react';

import type { LogEntry } from '../types';
import { streamContainerLogs } from '../lib/api';
import { LOG_VIEWER } from '../lib/constants';

// ============================================================================
// Types
// ============================================================================

export interface UseLogStreamOptions {
  /** Container ID to stream logs from */
  containerId: string | null;
  /** Automatically connect when containerId is set */
  autoConnect?: boolean;
  /** Maximum number of log lines to keep in buffer */
  maxLines?: number;
}

export interface UseLogStreamReturn {
  /** Accumulated log entries */
  logs: LogEntry[];
  /** Whether stream is currently connected */
  isConnected: boolean;
  /** Whether currently connecting */
  isConnecting: boolean;
  /** Error from stream connection */
  error: string | null;
  /** Manually connect to the log stream */
  connect: () => void;
  /** Disconnect from the log stream */
  disconnect: () => void;
  /** Clear all accumulated logs */
  clearLogs: () => void;
  /** Reconnect to the stream (disconnect then connect) */
  reconnect: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for streaming container logs with auto-reconnect
 *
 * @example
 * ```tsx
 * const { logs, isConnected, connect, disconnect, clearLogs } = useLogStream({
 *   containerId: 'abc123',
 *   autoConnect: true,
 *   maxLines: 1000,
 * });
 * ```
 */
export function useLogStream(
  options: UseLogStreamOptions
): UseLogStreamReturn {
  const {
    containerId,
    autoConnect = true,
    maxLines = LOG_VIEWER.MAX_LINES,
  } = options;

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Refs for cleanup and state tracking
  const cleanupRef = useRef<(() => void) | null>(null);
  const isMountedRef = useRef(true);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const autoConnectRef = useRef(autoConnect);

  // Keep autoConnect ref in sync
  useEffect(() => {
    autoConnectRef.current = autoConnect;
  }, [autoConnect]);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (isMountedRef.current) {
      setIsConnected(false);
      setIsConnecting(false);
    }
  }, []);

  // Connect to log stream
  const connect = useCallback(() => {
    if (!containerId || !isMountedRef.current) {
      return;
    }

    // Clean up existing connection first
    cleanup();

    setIsConnecting(true);
    setError(null);

    try {
      cleanupRef.current = streamContainerLogs(
        containerId,
        // onLog
        (entry: LogEntry) => {
          if (!isMountedRef.current) return;

          setLogs((prev) => {
            const newLogs = [...prev, entry];
            // Trim to maxLines
            if (newLogs.length > maxLines) {
              return newLogs.slice(-maxLines);
            }
            return newLogs;
          });
        },
        // onConnected
        () => {
          if (!isMountedRef.current) return;
          setIsConnecting(false);
          setIsConnected(true);
          setError(null);
        },
        // onDisconnected
        () => {
          if (!isMountedRef.current) return;
          setIsConnected(false);
          setIsConnecting(false);
        },
        // onError
        (err: Error) => {
          if (!isMountedRef.current) return;
          setIsConnected(false);
          setIsConnecting(false);
          setError(err.message);
        }
      );
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to log stream';
      setError(errorMessage);
      setIsConnecting(false);
      setIsConnected(false);
    }
  }, [containerId, maxLines, cleanup]);

  // Disconnect from log stream
  const disconnect = useCallback(() => {
    cleanup();
  }, [cleanup]);

  // Clear logs
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Reconnect (disconnect then connect)
  const reconnect = useCallback(() => {
    disconnect();
    // Small delay before reconnect
    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, 100);
  }, [disconnect, connect]);

  // Auto-connect when containerId changes
  useEffect(() => {
    if (!containerId) {
      cleanup();
      return;
    }

    if (autoConnectRef.current) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [containerId, connect, cleanup]);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
      cleanup();
    };
  }, [cleanup]);

  return {
    logs,
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    clearLogs,
    reconnect,
  };
}

// ============================================================================
// Utility Hook: Log Stream with Filters
// ============================================================================

export interface LogLevel {
  debug: string;
  info: string;
  warning: string;
  error: string;
}

export interface UseLogStreamWithFiltersOptions extends UseLogStreamOptions {
  /** Minimum log level to display */
  minLevel?: 'debug' | 'info' | 'warning' | 'error';
  /** Search query to filter logs */
  searchQuery?: string;
}

export interface UseLogStreamWithFiltersReturn extends UseLogStreamReturn {
  /** Filtered log entries */
  filteredLogs: LogEntry[];
  /** Count of logs by level */
  counts: Record<string, number>;
}

/**
 * Hook for log streaming with filtering capabilities
 */
export function useLogStreamWithFilters(
  options: UseLogStreamWithFiltersOptions
): UseLogStreamWithFiltersReturn {
  const { containerId, autoConnect, maxLines, minLevel, searchQuery } = options;

  const baseResult = useLogStream({ containerId, autoConnect, maxLines });

  // Level priority for filtering
  const levelPriority: Record<string, number> = {
    debug: 0,
    info: 1,
    warning: 2,
    error: 3,
  };

  const filteredLogs = baseResult.logs.filter((log) => {
    // Filter by level
    if (minLevel) {
      const logLevel = log.level?.toLowerCase() || 'info';
      if (levelPriority[logLevel] < levelPriority[minLevel]) {
        return false;
      }
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const message = (log.message || '').toLowerCase();
      if (!message.includes(query)) {
        return false;
      }
    }

    return true;
  });

  // Count logs by level
  const counts = baseResult.logs.reduce(
    (acc, log) => {
      const level = log.level?.toLowerCase() || 'unknown';
      acc[level] = (acc[level] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return {
    ...baseResult,
    filteredLogs,
    counts,
  };
}

export default useLogStream;

/**
 * Control Room API Client
 * Type-safe API client specifically for the Control Room Dashboard
 */

import {
  dockerOrchestratorApi,
  ApiError,
} from '../../shared/lib/api-client';

import type {
  ContainerInfo,
  ContainerListResponse,
  ActionResponse,
  MetricsResponse,
  LogsResponse,
  DeploymentResponse,
  LogEntry,
  ContainerStatus,
} from '../../shared/types';

import type { LogFilters, TimeRange } from '../types';

// ============================================================================
// Re-export for convenience
// ============================================================================

export { ApiError };

// ============================================================================
// Control Room API Functions
// ============================================================================

/**
 * List all containers
 */
export async function listContainers(params?: {
  all?: boolean;
  status?: ContainerStatus | 'all';
  agent_id?: string;
}): Promise<ContainerListResponse> {
  return dockerOrchestratorApi.listContainers(params as {
    all?: boolean;
    status?: 'running' | 'stopped' | 'paused' | 'all';
    agent_id?: string;
  });
}

/**
 * Get container by ID
 */
export async function getContainer(containerId: string): Promise<ContainerInfo> {
  return dockerOrchestratorApi.getContainer(containerId);
}

/**
 * Start container
 */
export async function startContainer(containerId: string): Promise<ActionResponse> {
  return dockerOrchestratorApi.startContainer(containerId);
}

/**
 * Stop container
 */
export async function stopContainer(containerId: string, timeout?: number): Promise<ActionResponse> {
  return dockerOrchestratorApi.stopContainer(containerId, timeout);
}

/**
 * Restart container
 */
export async function restartContainer(containerId: string, timeout?: number): Promise<ActionResponse> {
  return dockerOrchestratorApi.restartContainer(containerId, timeout);
}

/**
 * Remove container
 */
export async function removeContainer(
  containerId: string,
  options?: { force?: boolean; remove_volumes?: boolean }
): Promise<void> {
  return dockerOrchestratorApi.removeContainer(containerId, options);
}

/**
 * Get container metrics
 */
export async function getContainerMetrics(containerId: string): Promise<MetricsResponse> {
  return dockerOrchestratorApi.getContainerMetrics(containerId);
}

/**
 * Get container logs (paginated)
 */
export async function getContainerLogs(
  containerId: string,
  params?: {
    tail?: number;
    since?: string;
    timestamps?: boolean;
    offset?: number;
    limit?: number;
  }
): Promise<LogsResponse> {
  return dockerOrchestratorApi.getContainerLogs(containerId, params);
}

/**
 * Create log stream connection (Server-Sent Events)
 * Returns a cleanup function to close the connection
 */
export function streamContainerLogs(
  containerId: string,
  onLog: (entry: LogEntry) => void,
  onConnected?: () => void,
  onDisconnected?: () => void,
  onError?: (error: Error) => void
): () => void {
  const baseUrl = process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:4522';
  const eventSource = new EventSource(`${baseUrl}/api/logs/${containerId}/stream`);

  eventSource.onopen = () => {
    onConnected?.();
  };

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.level && data.message && data.timestamp) {
        onLog(data as LogEntry);
      }
    } catch {
      // Non-JSON message, ignore
    }
  };

  eventSource.onerror = () => {
    onError?.(new Error('Log stream connection error'));
    onDisconnected?.();
    eventSource.close();
  };

  // Return cleanup function
  return () => {
    eventSource.close();
    onDisconnected?.();
  };
}

/**
 * Execute command in container
 */
export async function execInContainer(
  containerId: string,
  command: string[]
): Promise<{ exit_code: number; output: string }> {
  return dockerOrchestratorApi.execInContainer(containerId, command);
}

/**
 * Remove deployment
 */
export async function removeDeployment(deploymentId: string): Promise<void> {
  return dockerOrchestratorApi.removeDeployment(deploymentId);
}

/**
 * Health check
 */
export async function healthCheck() {
  return dockerOrchestratorApi.healthCheck();
}

// ============================================================================
// Polling Utilities
// ============================================================================

/**
 * Create a polling interval for container list updates
 */
export function createContainerPoller(
  callback: (containers: ContainerListResponse) => void,
  intervalMs: number = 10000
): () => void {
  let intervalId: NodeJS.Timeout | null = null;
  let isPolling = true;

  const poll = async () => {
    if (!isPolling) return;
    try {
      const result = await listContainers();
      callback(result);
    } catch (error) {
      console.error('Container poll error:', error);
    }
  };

  // Initial fetch
  poll();

  // Set up interval
  intervalId = setInterval(poll, intervalMs);

  // Return cleanup function
  return () => {
    isPolling = false;
    if (intervalId) {
      clearInterval(intervalId);
    }
  };
}

/**
 * Create a polling interval for metrics updates
 */
export function createMetricsPoller(
  containerId: string,
  callback: (metrics: MetricsResponse) => void,
  intervalMs: number = 5000
): () => void {
  let intervalId: NodeJS.Timeout | null = null;
  let isPolling = true;

  const poll = async () => {
    if (!isPolling) return;
    try {
      const result = await getContainerMetrics(containerId);
      callback(result);
    } catch (error) {
      console.error('Metrics poll error:', error);
    }
  };

  // Initial fetch
  poll();

  // Set up interval
  intervalId = setInterval(poll, intervalMs);

  // Return cleanup function
  return () => {
    isPolling = false;
    if (intervalId) {
      clearInterval(intervalId);
    }
  };
}

// ============================================================================
// React Query / SWR Keys
// ============================================================================

export const queryKeys = {
  containers: {
    list: (params?: Record<string, unknown>) => ['containers', 'list', params] as const,
    detail: (id: string) => ['containers', 'detail', id] as const,
    metrics: (id: string) => ['containers', 'metrics', id] as const,
    logs: (id: string, params?: Record<string, unknown>) => ['containers', 'logs', id, params] as const,
  },
  health: () => ['health'] as const,
} as const;

// ============================================================================
// Export all
// ============================================================================

export const controlRoomApi = {
  listContainers,
  getContainer,
  startContainer,
  stopContainer,
  restartContainer,
  removeContainer,
  getContainerMetrics,
  getContainerLogs,
  streamContainerLogs,
  execInContainer,
  removeDeployment,
  healthCheck,
  createContainerPoller,
  createMetricsPoller,
} as const;

export default controlRoomApi;

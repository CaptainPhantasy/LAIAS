/**
 * Control Room Types
 * Types specific to the Container Monitoring Dashboard
 */

// ============================================================================
// Import shared types directly
// ============================================================================

import type {
  ContainerInfo,
  ContainerListResponse,
  ResourceUsage,
  ActionResponse,
  MetricsResponse,
  LogsResponse,
  DeploymentResponse,
  HealthResponse,
  ErrorResponse,
  ContainerStatus,
  DeploymentStatus,
  LogLevel,
  ServiceHealthStatus,
  LogEntry,
  LogStreamEvent,
  AsyncState,
  LoadingState,
} from '../../shared/types'; // Re-export common shared types for convenience

// Re-export shared types for use throughout the control-room
export type {
  ContainerInfo,
  ContainerListResponse,
  ResourceUsage,
  ActionResponse,
  MetricsResponse,
  LogsResponse,
  DeploymentResponse,
  HealthResponse,
  ErrorResponse,
  ContainerStatus,
  DeploymentStatus,
  LogLevel,
  ServiceHealthStatus,
  LogEntry,
  LogStreamEvent,
  AsyncState,
  LoadingState,
};

// ============================================================================
// Control Room Specific Types
// ============================================================================

/**
 * Dashboard KPI metric
 */
export interface DashboardMetric {
  id: string;
  label: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  status: 'success' | 'warning' | 'error' | 'neutral';
}

/**
 * Container action types
 */
export type ContainerAction = 'start' | 'stop' | 'restart' | 'remove' | 'logs';

/**
 * Container filter state
 */
export interface ContainerFilters {
  search: string;
  status: ContainerStatus | 'all';
  agentId?: string;
}

/**
 * Log viewer state
 */
export interface LogViewerState {
  containerId: string;
  containerName: string;
  logs: LogEntry[];
  isLoading: boolean;
  isStreaming: boolean;
  autoScroll: boolean;
  searchQuery: string;
  levelFilter: LogLevel[];
  hasMore: boolean;
  offset: number;
}

/**
 * Log viewer filters
 */
export interface LogFilters {
  search: string;
  levels: LogLevel[];
  autoScroll: boolean;
}

/**
 * Metrics chart data point
 */
export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

/**
 * Container metrics history
 */
export interface ContainerMetricsHistory {
  containerId: string;
  cpu: MetricDataPoint[];
  memory: MetricDataPoint[];
  network: {
    rx: MetricDataPoint[];
    tx: MetricDataPoint[];
  };
}

/**
 * Control Room state (for Zustand or similar)
 */
export interface ControlRoomState {
  // Container list
  containers: ContainerInfo[];
  isLoadingContainers: boolean;
  containerError: string | null;
  filters: ContainerFilters;

  // Selected container
  selectedContainerId: string | null;
  selectedContainer: ContainerInfo | null;

  // Metrics
  metricsHistory: ContainerMetricsHistory | null;

  // Log viewer
  logViewer: LogViewerState | null;

  // Actions
  setContainers: (containers: ContainerInfo[]) => void;
  setFilters: (filters: Partial<ContainerFilters>) => void;
  selectContainer: (containerId: string | null) => void;
  setLogViewer: (state: LogViewerState | null) => void;
  addLogEntry: (entry: LogEntry) => void;
  clearLogs: () => void;
  setAutoScroll: (enabled: boolean) => void;
}

/**
 * Container card props
 */
export interface ContainerCardProps {
  containerId: string;
  name: string;
  agentName: string;
  status: ContainerStatus;
  resourceUsage?: ResourceUsage;
  createdAt: string;
  startedAt?: string;
  onStart: () => void;
  onStop: () => void;
  onRestart: () => void;
  onRemove: () => void;
  onViewLogs: () => void;
  onViewMetrics: () => void;
}

/**
 * Status badge variant
 */
export type StatusBadgeVariant = 'running' | 'stopped' | 'paused' | 'error' | 'pending';

/**
 * Status badge config
 */
export const STATUS_BADGE_CONFIG: Record<StatusBadgeVariant, {
  label: string;
  color: string;
  pulse: boolean;
}> = {
  running: { label: 'Running', color: 'success', pulse: true },
  stopped: { label: 'Stopped', color: 'neutral', pulse: false },
  paused: { label: 'Paused', color: 'warning', pulse: false },
  error: { label: 'Error', color: 'error', pulse: false },
  pending: { label: 'Pending', color: 'warning', pulse: true },
};

/**
 * Quick action button config
 */
export interface QuickAction {
  id: ContainerAction;
  label: string;
  icon: string;
  variant: 'primary' | 'secondary' | 'danger' | 'ghost';
  confirmMessage?: string;
  disabledWhen?: ContainerStatus[];
}

/**
 * Available quick actions
 */
export const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'start',
    label: 'Start',
    icon: 'play',
    variant: 'primary',
    disabledWhen: ['running'],
  },
  {
    id: 'stop',
    label: 'Stop',
    icon: 'square',
    variant: 'secondary',
    confirmMessage: 'Stop this container?',
    disabledWhen: ['stopped', 'exited'],
  },
  {
    id: 'restart',
    label: 'Restart',
    icon: 'refresh',
    variant: 'secondary',
    confirmMessage: 'Restart this container?',
  },
  {
    id: 'logs',
    label: 'Logs',
    icon: 'file-text',
    variant: 'ghost',
  },
  {
    id: 'remove',
    label: 'Remove',
    icon: 'trash',
    variant: 'danger',
    confirmMessage: 'Permanently remove this container?',
    disabledWhen: ['running'],
  },
];

/**
 * Chart time range options
 */
export type TimeRange = '1h' | '6h' | '24h' | '7d';

/**
 * Dashboard refresh interval options
 */
export type RefreshInterval = 5000 | 10000 | 30000 | 60000;

/**
 * Settings for Control Room
 */
export interface ControlRoomSettings {
  refreshInterval: RefreshInterval;
  defaultTimeRange: TimeRange;
  showResourceUsage: boolean;
  compactMode: boolean;
}

/**
 * Default settings
 */
export const DEFAULT_SETTINGS: ControlRoomSettings = {
  refreshInterval: 10000,
  defaultTimeRange: '1h',
  showResourceUsage: true,
  compactMode: false,
};

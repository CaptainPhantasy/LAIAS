/**
 * Application-wide constants
 */

// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_DOCKER_ORCHESTRATOR_URL || 'http://localhost:4522';

// Polling intervals (in milliseconds)
export const POLLING_INTERVALS = {
  CONTAINERS: 10000,      // 10 seconds
  METRICS: 5000,          // 5 seconds
  HEALTH: 30000,          // 30 seconds
} as const;

// Log viewer settings
export const LOG_VIEWER = {
  MAX_LINES: 10000,
  DEFAULT_TAIL: 500,
  AUTO_SCROLL_THRESHOLD: 200, // pixels from bottom
  VIRTUAL_OVERSCAN: 20,
  ESTIMATED_LINE_HEIGHT: 24,
} as const;

// Metrics chart settings
export const METRICS_CHART = {
  MAX_DATA_POINTS: 60,
  UPDATE_INTERVAL: 5000,
  ANIMATION_DURATION: 300,
} as const;

// Container statuses
export const CONTAINER_STATUS = {
  RUNNING: 'running',
  STOPPED: 'stopped',
  PAUSED: 'paused',
  EXITED: 'exited',
  ERROR: 'error',
} as const;

// Status colors mapping
export const STATUS_COLORS = {
  running: 'success',
  stopped: 'neutral',
  paused: 'warning',
  exited: 'neutral',
  error: 'error',
  pending: 'warning',
} as const;

// Log levels
export const LOG_LEVELS = ['debug', 'info', 'warning', 'error'] as const;

// Log level colors
export const LOG_LEVEL_COLORS = {
  debug: 'text-muted',
  info: 'text-info',
  warning: 'text-warning',
  error: 'text-error',
} as const;

// Breakpoints (matching Tailwind)
export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

// Sidebar configuration
export const SIDEBAR = {
  WIDTH: 240,
  COLLAPSED_WIDTH: 64,
} as const;

// Top bar height
export const TOP_BAR_HEIGHT = 56;

// Navigation items
export const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', href: '/', icon: 'layout-dashboard' },
  { id: 'containers', label: 'Containers', href: '/containers', icon: 'box' },
  { id: 'metrics', label: 'Metrics', href: '/metrics', icon: 'activity' },
] as const;

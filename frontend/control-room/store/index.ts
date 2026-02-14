/**
 * Control Room Stores
 * Barrel exports for all Zustand stores
 */

// Containers Store
export {
  useContainersStore,
  useSelectedContainer,
  useFilteredContainers,
  useContainerById,
  useContainersByStatus,
} from './containers-store';
export type { ContainersState } from './containers-store';

// Log Viewer Store
export {
  useLogViewerStore,
  useFilteredLogs,
  useLogsByLevel,
  useLogCount,
  useFilteredLogCount,
  useLogActions,
} from './log-viewer-store';
export type { LogViewerState } from './log-viewer-store';

// Settings Store
export {
  useSettingsStore,
  useRefreshInterval,
  useTimeRange,
  useTheme,
  useSidebarCollapsed,
  useShowResourceUsage,
  useCompactMode,
  useSettingsActions,
} from './settings-store';
export type { SettingsState } from './settings-store';

// Re-export store types for convenience
export type StoreTypes = {
  containers: import('./containers-store').ContainersState;
  logViewer: import('./log-viewer-store').LogViewerState;
  settings: import('./settings-store').SettingsState;
};

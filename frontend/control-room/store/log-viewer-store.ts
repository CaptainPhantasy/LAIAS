/**
 * Log Viewer Store
 * Manages log streaming, filtering, and viewer state
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { LogEntry, LogLevel } from '../types';

export interface LogViewerState {
  // State
  logs: LogEntry[];
  isLoading: boolean;
  isStreaming: boolean;
  autoScroll: boolean;
  searchQuery: string;
  levelFilter: LogLevel[];
  containerId: string | null;

  // Actions
  addLog: (log: LogEntry) => void;
  addLogs: (logs: LogEntry[]) => void;
  clearLogs: () => void;
  setAutoScroll: (enabled: boolean) => void;
  setSearchQuery: (query: string) => void;
  setLevelFilter: (levels: LogLevel[]) => void;
  setStreaming: (streaming: boolean) => void;
  setContainerId: (id: string | null) => void;
  setLoading: (loading: boolean) => void;

  // Selectors
  getFilteredLogs: () => LogEntry[];
  getLogsByLevel: (level: LogLevel) => LogEntry[];
  getLogCount: () => number;
  getFilteredLogCount: () => number;
}

const DEFAULT_LEVEL_FILTER: LogLevel[] = ['debug', 'info', 'warning', 'error'];

const createLogSelectors = (state: LogViewerState) => ({
  getFilteredLogs: () => {
    let filtered = state.logs;

    // Level filter
    if (state.levelFilter.length > 0) {
      filtered = filtered.filter((log) =>
        state.levelFilter.includes(log.level)
      );
    }

    // Search filter
    if (state.searchQuery) {
      const query = state.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (log) =>
          log.message.toLowerCase().includes(query) ||
          log.raw?.toLowerCase().includes(query)
      );
    }

    return filtered;
  },

  getLogsByLevel: (level: LogLevel) =>
    state.logs.filter((log) => log.level === level),

  getLogCount: () => state.logs.length,

  getFilteredLogCount: () => {
    let filtered = state.logs;

    if (state.levelFilter.length > 0) {
      filtered = filtered.filter((log) =>
        state.levelFilter.includes(log.level)
      );
    }

    if (state.searchQuery) {
      const query = state.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (log) =>
          log.message.toLowerCase().includes(query) ||
          log.raw?.toLowerCase().includes(query)
      );
    }

    return filtered.length;
  },
});

export const useLogViewerStore = create<LogViewerState>()(
  devtools(
    (set, get) => ({
      // Initial state
      logs: [],
      isLoading: false,
      isStreaming: false,
      autoScroll: true,
      searchQuery: '',
      levelFilter: DEFAULT_LEVEL_FILTER,
      containerId: null,

      // Actions
      addLog: (log) =>
        set(
          (state) => ({
            logs: [...state.logs, log],
          }),
          false,
          'logViewer/addLog'
        ),

      addLogs: (logs) =>
        set(
          (state) => ({
            logs: [...state.logs, ...logs],
          }),
          false,
          'logViewer/addLogs'
        ),

      clearLogs: () =>
        set({ logs: [] }, false, 'logViewer/clearLogs'),

      setAutoScroll: (autoScroll) =>
        set({ autoScroll }, false, 'logViewer/setAutoScroll'),

      setSearchQuery: (searchQuery) =>
        set({ searchQuery }, false, 'logViewer/setSearchQuery'),

      setLevelFilter: (levelFilter) =>
        set({ levelFilter }, false, 'logViewer/setLevelFilter'),

      setStreaming: (isStreaming) =>
        set({ isStreaming }, false, 'logViewer/setStreaming'),

      setContainerId: (containerId) =>
        set({ containerId }, false, 'logViewer/setContainerId'),

      setLoading: (isLoading) =>
        set({ isLoading }, false, 'logViewer/setLoading'),

      // Selectors
      ...createLogSelectors(get() as LogViewerState),
    }),
    { name: 'LogViewerStore' }
  )
);

// Selector hooks for external use
export const useFilteredLogs = () =>
  useLogViewerStore((state) => state.getFilteredLogs());

export const useLogsByLevel = (level: LogLevel) =>
  useLogViewerStore((state) => state.getLogsByLevel(level));

export const useLogCount = () =>
  useLogViewerStore((state) => state.getLogCount());

export const useFilteredLogCount = () =>
  useLogViewerStore((state) => state.getFilteredLogCount());

// Action hooks for convenience
export const useLogActions = () =>
  useLogViewerStore((state) => ({
    addLog: state.addLog,
    addLogs: state.addLogs,
    clearLogs: state.clearLogs,
    setAutoScroll: state.setAutoScroll,
    setSearchQuery: state.setSearchQuery,
    setLevelFilter: state.setLevelFilter,
    setStreaming: state.setStreaming,
    setContainerId: state.setContainerId,
  }));

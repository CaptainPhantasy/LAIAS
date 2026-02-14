/**
 * Settings Store
 * Manages user preferences with localStorage persistence
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { ControlRoomSettings, RefreshInterval, TimeRange } from '../types';
import { DEFAULT_SETTINGS } from '../types';

export interface SettingsState extends ControlRoomSettings {
  // UI State
  theme: 'dark' | 'light';
  sidebarCollapsed: boolean;

  // Actions
  setRefreshInterval: (interval: RefreshInterval) => void;
  setTimeRange: (range: TimeRange) => void;
  setTheme: (theme: 'dark' | 'light') => void;
  toggleSidebar: () => void;
  setShowResourceUsage: (show: boolean) => void;
  setCompactMode: (compact: boolean) => void;
  reset: () => void;
}

const STORAGE_KEY = 'control-room-settings';

export const useSettingsStore = create<SettingsState>()(
  devtools(
    persist(
      (set) => ({
        // Default settings from types
        refreshInterval: DEFAULT_SETTINGS.refreshInterval,
        defaultTimeRange: DEFAULT_SETTINGS.defaultTimeRange,
        showResourceUsage: DEFAULT_SETTINGS.showResourceUsage,
        compactMode: DEFAULT_SETTINGS.compactMode,

        // UI defaults
        theme: 'dark',
        sidebarCollapsed: false,

        // Actions
        setRefreshInterval: (refreshInterval) =>
          set({ refreshInterval }, false, 'settings/setRefreshInterval'),

        setTimeRange: (defaultTimeRange) =>
          set({ defaultTimeRange }, false, 'settings/setTimeRange'),

        setTheme: (theme) =>
          set({ theme }, false, 'settings/setTheme'),

        toggleSidebar: () =>
          set(
            (state) => ({ sidebarCollapsed: !state.sidebarCollapsed }),
            false,
            'settings/toggleSidebar'
          ),

        setShowResourceUsage: (showResourceUsage) =>
          set({ showResourceUsage }, false, 'settings/setShowResourceUsage'),

        setCompactMode: (compactMode) =>
          set({ compactMode }, false, 'settings/setCompactMode'),

        reset: () =>
          set(
            {
              refreshInterval: DEFAULT_SETTINGS.refreshInterval,
              defaultTimeRange: DEFAULT_SETTINGS.defaultTimeRange,
              showResourceUsage: DEFAULT_SETTINGS.showResourceUsage,
              compactMode: DEFAULT_SETTINGS.compactMode,
              theme: 'dark',
              sidebarCollapsed: false,
            },
            false,
            'settings/reset'
          ),
      }),
      {
        name: STORAGE_KEY,
        version: 1,
        // Only persist specific fields
        partialize: (state) => ({
          refreshInterval: state.refreshInterval,
          defaultTimeRange: state.defaultTimeRange,
          showResourceUsage: state.showResourceUsage,
          compactMode: state.compactMode,
          theme: state.theme,
          sidebarCollapsed: state.sidebarCollapsed,
        }),
      }
    ),
    { name: 'SettingsStore' }
  )
);

// Selector hooks for external use
export const useRefreshInterval = () =>
  useSettingsStore((state) => state.refreshInterval);

export const useTimeRange = () =>
  useSettingsStore((state) => state.defaultTimeRange);

export const useTheme = () =>
  useSettingsStore((state) => state.theme);

export const useSidebarCollapsed = () =>
  useSettingsStore((state) => state.sidebarCollapsed);

export const useShowResourceUsage = () =>
  useSettingsStore((state) => state.showResourceUsage);

export const useCompactMode = () =>
  useSettingsStore((state) => state.compactMode);

// Action hooks for convenience
export const useSettingsActions = () =>
  useSettingsStore((state) => ({
    setRefreshInterval: state.setRefreshInterval,
    setTimeRange: state.setTimeRange,
    setTheme: state.setTheme,
    toggleSidebar: state.toggleSidebar,
    setShowResourceUsage: state.setShowResourceUsage,
    setCompactMode: state.setCompactMode,
    reset: state.reset,
  }));

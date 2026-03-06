/**
 * Keyboard Navigation Implementation
 * Per Blueprint Section E.1
 */

import { useEffect, useCallback, useRef } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  action: () => void;
  description?: string;
}

export interface KeyboardNavigationConfig {
  /**
   * Enable global "?" shortcut for keyboard shortcuts modal
   */
  enableHelpShortcut?: boolean;
  /**
   * Callback to show keyboard shortcuts modal
   */
  onShowShortcuts?: () => void;
  /**
   * Additional shortcuts to register
   */
  shortcuts?: KeyboardShortcut[];
}

// ============================================================================
// Keyboard Shortcuts Hook
// ============================================================================

export function useKeyboardShortcuts(config: KeyboardNavigationConfig = {}) {
  const { enableHelpShortcut = true, onShowShortcuts, shortcuts = [] } = config;

  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Global "?" shortcut for keyboard help
      if (enableHelpShortcut && e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // Only trigger if not in an input field
        const target = e.target as HTMLElement;
        const isInput =
          target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable;

        if (!isInput && onShowShortcuts) {
          e.preventDefault();
          onShowShortcuts();
          return;
        }
      }

      // Process custom shortcuts
      for (const shortcut of shortcutsRef.current) {
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatch = !!shortcut.ctrl === (e.ctrlKey || e.metaKey);
        const shiftMatch = !!shortcut.shift === e.shiftKey;
        const altMatch = !!shortcut.alt === e.altKey;
        const metaMatch = !!shortcut.meta === e.metaKey;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
          e.preventDefault();
          shortcut.action();
          return;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [enableHelpShortcut, onShowShortcuts]);
}

// ============================================================================
// Arrow Key Navigation Hook
// ============================================================================

export type NavigationMode = 'list' | 'grid' | 'tabs';

export interface ArrowNavigationConfig {
  /**
   * Items to navigate through
   */
  items: string[];
  /**
   * Currently selected item
   */
  selectedId?: string;
  /**
   * Callback when selection changes
   */
  onSelect?: (id: string) => void;
  /**
   * Whether navigation is enabled
   */
  enabled?: boolean;
  /**
   * Whether to wrap around at ends
   */
  wrap?: boolean;
  /**
   * Whether this is a grid (uses all arrow keys) or list (uses up/down) or tabs (uses left/right)
   */
  mode?: NavigationMode;
  /**
   * Number of columns for grid mode
   */
  columns?: number;
}

export function useArrowNavigation(config: ArrowNavigationConfig) {
  const {
    items,
    selectedId,
    onSelect,
    enabled = true,
    wrap = true,
    mode = 'list',
    columns = 1,
  } = config;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled || !selectedId || !onSelect) return;

      const currentIndex = items.indexOf(selectedId);
      if (currentIndex === -1) return;

      let nextIndex = currentIndex;

      switch (e.key) {
        case 'ArrowUp':
          if (mode === 'grid') {
            e.preventDefault();
            nextIndex = currentIndex - columns;
            if (nextIndex < 0) {
              nextIndex = wrap ? items.length + nextIndex : 0;
            }
          } else if (mode === 'list') {
            e.preventDefault();
            nextIndex = currentIndex - 1;
            if (nextIndex < 0) {
              nextIndex = wrap ? items.length - 1 : 0;
            }
          }
          break;

        case 'ArrowDown':
          if (mode === 'grid') {
            e.preventDefault();
            nextIndex = currentIndex + columns;
            if (nextIndex >= items.length) {
              nextIndex = wrap ? nextIndex - items.length : items.length - 1;
            }
          } else if (mode === 'list') {
            e.preventDefault();
            nextIndex = currentIndex + 1;
            if (nextIndex >= items.length) {
              nextIndex = wrap ? 0 : items.length - 1;
            }
          }
          break;

        case 'ArrowLeft':
          if (mode === 'grid' || mode === 'tabs') {
            e.preventDefault();
            nextIndex = currentIndex - 1;
            if (nextIndex < 0) {
              nextIndex = wrap ? items.length - 1 : 0;
            }
          }
          break;

        case 'ArrowRight':
          if (mode === 'grid' || mode === 'tabs') {
            e.preventDefault();
            nextIndex = currentIndex + 1;
            if (nextIndex >= items.length) {
              nextIndex = wrap ? 0 : items.length - 1;
            }
          }
          break;

        case 'Enter':
        case ' ':
          // Enter/Space are handled by the component itself
          return;

        default:
          return;
      }

      if (nextIndex !== currentIndex && items[nextIndex] !== undefined) {
        onSelect(items[nextIndex]);
      }
    },
    [items, selectedId, onSelect, enabled, wrap, mode, columns]
  );

  useEffect(() => {
    if (!enabled) return;

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, enabled]);
}

// ============================================================================
// Tab Navigation Hook
// ============================================================================

export interface TabNavigationConfig {
  tabs: string[];
  activeTab: string;
  onTabChange: (tab: string) => void;
  enabled?: boolean;
}

export function useTabNavigation(config: TabNavigationConfig) {
  const { tabs, activeTab, onTabChange, enabled = true } = config;

  useArrowNavigation({
    items: tabs,
    selectedId: activeTab,
    onSelect: onTabChange,
    enabled,
    mode: 'tabs',
    wrap: true,
  });
}

// ============================================================================
// Log Viewer Shortcuts Hook
// ============================================================================

export interface LogViewerShortcutsConfig {
  onSearch?: () => void;
  onCopy?: () => void;
  enabled?: boolean;
}

export function useLogViewerShortcuts(config: LogViewerShortcutsConfig) {
  const { onSearch, onCopy, enabled = true } = config;

  const shortcuts: KeyboardShortcut[] = [];

  if (onSearch) {
    shortcuts.push({
      key: 'f',
      description: 'Focus search',
      action: onSearch,
    });
  }

  if (onCopy) {
    shortcuts.push({
      key: 'c',
      description: 'Copy selected log',
      action: onCopy,
    });
  }

  useKeyboardShortcuts({
    shortcuts: enabled ? shortcuts : [],
  });
}

// ============================================================================
// Code Editor Shortcuts Hook
// ============================================================================

export interface CodeEditorShortcutsConfig {
  onSave?: () => void;
  enabled?: boolean;
}

export function useCodeEditorShortcuts(config: CodeEditorShortcutsConfig) {
  const { onSave, enabled = true } = config;

  const shortcuts: KeyboardShortcut[] = [];

  if (onSave) {
    shortcuts.push({
      key: 's',
      ctrl: true,
      description: 'Save',
      action: onSave,
    });
  }

  useKeyboardShortcuts({
    shortcuts: enabled ? shortcuts : [],
  });
}

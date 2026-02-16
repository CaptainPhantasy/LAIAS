'use client';

import { memo } from 'react';
import { TOP_BAR_HEIGHT } from '@/lib/constants';
import { cn } from '@/lib/utils';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

interface TopBarProps {
  title?: string;
  connectionStatus?: ConnectionStatus;
  theme?: 'dark' | 'light';
}

const STATUS_LABELS: Record<ConnectionStatus, string> = {
  connected: 'Connected',
  connecting: 'Connecting...',
  disconnected: 'Disconnected',
};

const STATUS_CLASSES: Record<ConnectionStatus, string> = {
  connected: 'connection-dot--connected',
  connecting: 'connection-dot--connecting',
  disconnected: 'connection-dot--disconnected',
};

export const TopBar = memo(function TopBar({
  title = 'Dashboard',
  connectionStatus = 'connected',
  theme,
}: TopBarProps) {
  return (
    <header
      className={cn(
        'flex items-center justify-between border-b border-border bg-surface',
        'sticky top-0 z-40 px-4 md:px-6'
      )}
      style={{ height: `${TOP_BAR_HEIGHT}px` }}
    >
      {/* Left: Brand/Logo - only show on mobile (sidebar hidden) */}
      <div className="flex items-center gap-3 md:hidden">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-accent-cyan to-accent-purple">
          <span className="text-sm font-bold text-white">L</span>
        </div>
        <span className="text-lg font-semibold text-gradient-brand">
          LAIAS
        </span>
      </div>
      
      {/* Desktop: Breadcrumb/Context area */}
      <div className="hidden md:flex items-center gap-2 text-text-2">
        {/* Intentionally empty on desktop - sidebar has branding */}
      </div>

      {/* Center: Page context - only show on mobile */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 md:hidden">
        <h1 className="text-base font-semibold text-text">
          {title}
        </h1>
      </div>
      
      {/* Desktop: Show connection status centered as context */}
      <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 items-center gap-2">
        <span
          className={cn('connection-dot', STATUS_CLASSES[connectionStatus])}
          aria-hidden="true"
        />
        <span className="text-sm font-medium text-text-2">
          {STATUS_LABELS[connectionStatus]}
        </span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Connection Status - only show on mobile (desktop shows in center) */}
        <div className="flex items-center gap-2 md:hidden">
          <span
            className={cn('connection-dot', STATUS_CLASSES[connectionStatus])}
            aria-hidden="true"
          />
        </div>

        {/* Theme Toggle */}
        <button
          className={cn(
            'rounded-lg p-2 text-text-3 transition-colors',
            'hover:bg-surface-2 hover:text-text-2',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary'
          )}
          aria-label="Toggle theme"
          type="button"
          tabIndex={0}
        >
          {/* Placeholder icon - replace with Sun/Moon when ready */}
          <svg
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
            aria-label="Theme toggle"
          >
            <title>Toggle theme</title>
            <circle
              cx="12"
              cy="12"
              r="4"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <path
              d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>
    </header>
  );
});

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  LayoutDashboard,
  Box,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  type LucideIcon,
} from 'lucide-react';
import { NAV_ITEMS, SIDEBAR } from '@/lib/constants';
import { cn } from '@/lib/utils';

// Icon mapping for navigation items
const ICON_MAP: Record<string, LucideIcon> = {
  'layout-dashboard': LayoutDashboard,
  'box': Box,
  'activity': Activity,
  'settings': Settings,
};

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export function Sidebar({ collapsed = false, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(collapsed);

  const handleToggle = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    onToggle?.();
  };

  const sidebarWidth = isCollapsed ? `${SIDEBAR.COLLAPSED_WIDTH}px` : `${SIDEBAR.WIDTH}px`;

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-50 flex h-screen flex-col border-r border-border bg-surface transition-all duration-200 ease-in-out',
        'md:relative md:top-auto md:z-0'
      )}
      style={{ width: sidebarWidth }}
    >
      {/* Brand Section */}
      <div className="flex h-[56px] items-center justify-between border-b border-border px-4">
        {!isCollapsed && (
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-accent-cyan to-accent-purple">
              <span className="text-sm font-bold text-white">L</span>
            </div>
            <span className="text-lg font-semibold text-gradient-brand">
              LAIAS
            </span>
          </Link>
        )}
        {isCollapsed && (
          <Link href="/" className="flex items-center justify-center w-full">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-accent-cyan to-accent-purple">
              <span className="text-sm font-bold text-white">L</span>
            </div>
          </Link>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden p-2">
        <ul className="flex flex-col gap-1" role="menubar" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = ICON_MAP[item.icon];
            const isActive = pathname === item.href;

            return (
              <li key={item.id} role="none">
                <Link
                  href={item.href}
                  role="menuitem"
                  className={cn(
                    'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all duration-150',
                    'hover:bg-surface-2',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary',
                    isActive && 'bg-surface-2'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {/* Active state indicator */}
                  {isActive && (
                    <span
                      className={cn(
                        'absolute left-0 top-1/2 -translate-y-1/2 h-8 w-0.5 rounded-r-full',
                        'bg-accent-cyan glow-cyan'
                      )}
                    />
                  )}

                  {/* Icon */}
                  <span
                    className={cn(
                      'flex-shrink-0 transition-colors',
                      isActive ? 'text-accent-cyan' : 'text-text-3 group-hover:text-text-2'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </span>

                  {/* Label */}
                  {!isCollapsed && (
                    <span
                      className={cn(
                        'truncate text-sm font-medium transition-colors',
                        isActive ? 'text-text' : 'text-text-2'
                      )}
                    >
                      {item.label}
                    </span>
                  )}

                  {/* Tooltip for collapsed state */}
                  {isCollapsed && (
                    <span className="sr-only">{item.label}</span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Toggle Button */}
      <div className="border-t border-border p-2">
        <button
          onClick={handleToggle}
          className={cn(
            'flex w-full items-center justify-center gap-2 rounded-lg p-2.5',
            'text-text-3 transition-all duration-150',
            'hover:bg-surface-2 hover:text-text-2',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary'
          )}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          type="button"
        >
          {isCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <>
              <span className="text-sm">Collapse</span>
              <ChevronLeft className="h-5 w-5" />
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

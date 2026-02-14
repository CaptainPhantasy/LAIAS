'use client';

import { useState, useEffect } from 'react';
import { Sidebar } from './sidebar';
import { TopBar } from './top-bar';
import { cn } from '@/lib/utils';
import { SIDEBAR } from '@/lib/constants';

interface AppShellProps {
  children: React.ReactNode;
  title?: string;
}

export function AppShell({ children, title }: AppShellProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Handle responsive behavior
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Auto-collapse on mobile
  useEffect(() => {
    if (isMobile) {
      setIsCollapsed(true);
    }
  }, [isMobile]);

  const sidebarWidth = isCollapsed ? SIDEBAR.COLLAPSED_WIDTH : SIDEBAR.WIDTH;

  return (
    <div
      className={cn(
        'min-h-screen bg-bg-primary',
        // Mobile: overlay sidebar when expanded
        isMobile && !isCollapsed && 'overflow-hidden'
      )}
    >
      <div
        className={cn(
          'transition-all duration-200 ease-in-out',
          // Grid layout for desktop
          'md:grid md:grid-cols-[auto_1fr]',
          'md:grid-rows-[auto_1fr]',
          'md:grid-areas-[\"header-header\"\"sidebar-main\"]'
        )}
        style={
          isMobile
            ? undefined
            : {
                gridTemplateColumns: `${sidebarWidth}px 1fr`,
              }
        }
      >
        {/* Sidebar */}
        <div
          className={cn(
            'md:area-sidebar',
            // Mobile overlay behavior
            isMobile &&
              !isCollapsed &&
              'fixed inset-0 z-50 bg-bg-primary/80 backdrop-blur-sm'
          )}
        >
          <div
            className={cn(
              // Mobile: inset sidebar with transition
              isMobile && 'h-full'
            )}
          >
            <Sidebar
              collapsed={isCollapsed}
              onToggle={() => setIsCollapsed(!isCollapsed)}
            />
          </div>

          {/* Mobile overlay backdrop */}
          {isMobile && !isCollapsed && (
            <button
              className="fixed inset-0 z-40 bg-bg-primary/50"
              onClick={() => setIsCollapsed(true)}
              aria-label="Close sidebar"
            />
          )}
        </div>

        {/* Header (Top Bar) */}
        <div className="md:area-header">
          <TopBar title={title} />
        </div>

        {/* Main Content Area */}
        <main
          className={cn(
            'md:area-main',
            'min-h-[calc(100vh-56px)]',
            'p-4 md:p-6 lg:p-8',
            'overflow-y-auto'
          )}
        >
          {children}
        </main>
      </div>
    </div>
  );
}

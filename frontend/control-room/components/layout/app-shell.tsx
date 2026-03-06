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
      {/* Mobile overlay backdrop - must be before sidebar for z-index */}
      {isMobile && !isCollapsed && (
        <button
          className="fixed inset-0 z-40 bg-bg-primary/50"
          onClick={() => setIsCollapsed(true)}
          aria-label="Close sidebar"
        />
      )}

      {/* Sidebar - fixed position on desktop */}
      <div
        className={cn(
          // Desktop: fixed sidebar
          'hidden md:block',
          // Mobile: show when expanded
          isMobile && !isCollapsed && 'block'
        )}
      >
        <div
          className={cn(
            // Desktop: fixed positioning
            'md:fixed md:top-0 md:left-0 md:h-screen',
            // Mobile: overlay behavior
            isMobile && !isCollapsed && 'fixed inset-0 z-50'
          )}
        >
          <Sidebar
            collapsed={isCollapsed}
            onToggle={() => setIsCollapsed(!isCollapsed)}
          />
        </div>
      </div>

      {/* Main wrapper - flex column for header + content */}
      <div
        className="flex flex-col min-h-screen"
        style={{
          // Desktop: offset for fixed sidebar
          marginLeft: isMobile ? 0 : sidebarWidth,
        }}
      >
        {/* Header (Top Bar) */}
        <header className="sticky top-0 z-30">
          <TopBar title={title} />
        </header>

        {/* Main Content Area */}
        <main
          className={cn(
            'flex-1',
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

'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  PlusCircle,
  FileCode2,
  Settings,
  Moon,
  Sun,
  Menu,
  X,
  ExternalLink,
  LayoutTemplate,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

// ============================================================================
// Types
// ============================================================================

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { label: 'Home', href: '/', icon: <Home className="w-5 h-5" /> },
  { label: 'Create Agent', href: '/create', icon: <PlusCircle className="w-5 h-5" /> },
  { label: 'Templates', href: '/templates', icon: <LayoutTemplate className="w-5 h-5" /> },
  { label: 'Agents', href: '/agents', icon: <FileCode2 className="w-5 h-5" /> },
  { label: 'Settings', href: '/settings', icon: <Settings className="w-5 h-5" /> },
];

// ============================================================================
// Sidebar Component
// ============================================================================

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed = false, onToggle }) => {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        'flex flex-col h-full bg-bg-secondary border-r border-border',
        'transition-all duration-300 ease-out',
        collapsed ? 'w-16' : 'w-56'
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-14 px-4 border-b border-border">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-cyan/20 flex items-center justify-center">
            <span className="text-accent-cyan font-bold text-sm">L</span>
          </div>
          {!collapsed && (
            <span className="text-lg font-semibold text-text-primary">Studio</span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg',
                'text-sm font-medium',
                'transition-all duration-150',
                'hover:bg-surface',
                isActive
                  ? 'bg-surface text-text-primary border-l-2 border-accent-cyan ml-[-2px] pl-[calc(0.75rem+2px)]'
                  : 'text-text-secondary hover:text-text-primary',
                collapsed && 'justify-center'
              )}
              title={collapsed ? item.label : undefined}
            >
              {item.icon}
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Control Room Link */}
      <div className="p-3 border-t border-border">
        <a
          href="http://localhost:3001"
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            'flex items-center gap-3 px-3 py-2.5 rounded-lg',
            'text-sm font-medium',
            'text-text-muted hover:text-text-secondary hover:bg-surface',
            'transition-all duration-150',
            collapsed && 'justify-center'
          )}
          title={collapsed ? 'Control Room' : undefined}
        >
          <ExternalLink className="w-5 h-5" />
          {!collapsed && <span>Control Room</span>}
        </a>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={onToggle}
        className={cn(
          'm-3 p-2 rounded-lg',
          'text-text-muted hover:text-text-secondary hover:bg-surface',
          'transition-colors duration-150',
          collapsed && 'mx-auto'
        )}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        <Menu className="w-5 h-5" />
      </button>
    </aside>
  );
};

// ============================================================================
// TopBar Component
// ============================================================================

interface TopBarProps {
  title?: string;
  actions?: React.ReactNode;
}

const TopBar: React.FC<TopBarProps> = ({ title, actions }) => {
  const [theme, setTheme] = React.useState<'dark' | 'light'>('dark');

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('laias-theme', newTheme);
  };

  // Initialize theme from localStorage
  React.useEffect(() => {
    const savedTheme = localStorage.getItem('laias-theme') as 'dark' | 'light' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
  }, []);

  return (
    <header className="flex items-center justify-between h-14 px-6 bg-surface border-b border-border">
      <div className="flex items-center gap-4">
        {title && (
          <h1 className="text-lg font-semibold text-text-primary">{title}</h1>
        )}
      </div>

      <div className="flex items-center gap-3">
        {actions}

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className={cn(
            'p-2 rounded-lg',
            'text-text-muted hover:text-text-secondary hover:bg-surface-2',
            'transition-colors duration-150'
          )}
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? (
            <Sun className="w-5 h-5" />
          ) : (
            <Moon className="w-5 h-5" />
          )}
        </button>
      </div>
    </header>
  );
};

// ============================================================================
// AppShell Component
// ============================================================================

interface AppShellProps {
  children: React.ReactNode;
  title?: string;
  actions?: React.ReactNode;
  fullWidth?: boolean;
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  title,
  actions,
  fullWidth = false,
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar title={title} actions={actions} />

        <main
          className={cn(
            'flex-1 overflow-auto',
            !fullWidth && 'p-6'
          )}
        >
          {children}
        </main>
      </div>
    </div>
  );
};

export { Sidebar, TopBar };

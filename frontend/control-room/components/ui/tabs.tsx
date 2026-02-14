'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface TabsProps {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  className?: string;
}

export interface TabListProps {
  children: React.ReactNode;
  className?: string;
}

export interface TabProps {
  value: string;
  disabled?: boolean;
  children: React.ReactNode;
  className?: string;
}

export interface TabPanelProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

// ============================================================================
// Context
// ============================================================================

interface TabsContextValue {
  selectedValue: string;
  onSelectTab: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | undefined>(undefined);

const useTabsContext = () => {
  const context = React.useContext(TabsContext);
  if (!context) {
    throw new Error('Tab components must be used within Tabs');
  }
  return context;
};

// ============================================================================
// Tabs Component
// ============================================================================

const Tabs = ({
  defaultValue,
  value: controlledValue,
  onValueChange,
  children,
  className,
}: TabsProps) => {
  const [uncontrolledValue, setUncontrolledValue] = React.useState(defaultValue || '');

  const isControlled = controlledValue !== undefined;
  const selectedValue = isControlled ? controlledValue : uncontrolledValue;

  const onSelectTab = (newValue: string) => {
    if (!isControlled) {
      setUncontrolledValue(newValue);
    }
    onValueChange?.(newValue);
  };

  return (
    <TabsContext.Provider value={{ selectedValue, onSelectTab }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
};

Tabs.displayName = 'Tabs';

// ============================================================================
// TabList Component
// ============================================================================

const TabList = ({ children, className }: TabListProps) => {
  return (
    <div
      role="tablist"
      className={cn(
        'inline-flex items-center gap-1 border-b border-border',
        className
      )}
    >
      {children}
    </div>
  );
};

TabList.displayName = 'TabList';

// ============================================================================
// Tab Component
// ============================================================================

const Tab = ({ value, disabled = false, children, className }: TabProps) => {
  const { selectedValue, onSelectTab } = useTabsContext();
  const isSelected = selectedValue === value;
  const tabRef = React.useRef<HTMLButtonElement>(null);

  const handleClick = () => {
    if (!disabled) {
      onSelectTab(value);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    // Handle arrow key navigation
    const parent = tabRef.current?.parentElement;
    if (!parent) return;

    const tabs = Array.from(
      parent.querySelectorAll('[role="tab"]:not([disabled])')
    );
    const currentIndex = tabs.indexOf(tabRef.current!);

    let nextIndex: number | null = null;

    switch (e.key) {
      case 'ArrowLeft':
        e.preventDefault();
        nextIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
        break;
      case 'ArrowRight':
        e.preventDefault();
        nextIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
        break;
      case 'Home':
        e.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        nextIndex = tabs.length - 1;
        break;
    }

    if (nextIndex !== null) {
      (tabs[nextIndex] as HTMLButtonElement).focus();
      (tabs[nextIndex] as HTMLButtonElement).click();
    }
  };

  return (
    <button
      ref={tabRef}
      role="tab"
      type="button"
      aria-selected={isSelected}
      aria-disabled={disabled}
      tabIndex={isSelected ? 0 : -1}
      disabled={disabled}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={cn(
        'relative px-4 py-2.5 text-sm font-medium transition-all duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary',
        'border-b-2 -mb-px',

        // Selected state
        isSelected
          ? 'text-accent-cyan border-accent-cyan'
          : 'text-text-secondary border-transparent hover:text-text-primary hover:border-border-strong',

        // Disabled state
        disabled && 'opacity-50 cursor-not-allowed pointer-events-none',

        className
      )}
    >
      {children}
    </button>
  );
};

Tab.displayName = 'Tab';

// ============================================================================
// TabPanel Component
// ============================================================================

const TabPanel = ({ value, children, className }: TabPanelProps) => {
  const { selectedValue } = useTabsContext();

  if (selectedValue !== value) return null;

  return (
    <div
      role="tabpanel"
      tabIndex={0}
      className={cn('py-4', className)}
    >
      {children}
    </div>
  );
};

TabPanel.displayName = 'TabPanel';

export { Tabs, TabList, Tab, TabPanel };

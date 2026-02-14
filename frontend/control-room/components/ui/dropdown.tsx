'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, Check } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface DropdownItemProps {
  label: string;
  value: string;
  icon?: React.ReactNode;
  disabled?: boolean;
  description?: string;
  onClick?: () => void;
}

export interface DropdownMenuProps {
  trigger: React.ReactNode;
  items: DropdownItemProps[];
  align?: 'start' | 'end' | 'center';
  width?: number;
  className?: string;
}

export interface DropdownContextValue {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  selectedIndex: number | null;
  setSelectedIndex: (index: number | null) => void;
}

// ============================================================================
// Context
// ============================================================================

const DropdownContext = React.createContext<DropdownContextValue | undefined>(undefined);

const useDropdownContext = () => {
  const context = React.useContext(DropdownContext);
  if (!context) {
    throw new Error('Dropdown components must be used within DropdownMenu');
  }
  return context;
};

// ============================================================================
// DropdownMenu Component
// ============================================================================

const DropdownMenu = ({
  trigger,
  items,
  align = 'start',
  width = 200,
  className,
}: DropdownMenuProps) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [selectedIndex, setSelectedIndex] = React.useState<number | null>(null);
  const triggerRef = React.useRef<HTMLDivElement>(null);
  const menuRef = React.useRef<HTMLDivElement>(null);

  // Close on click outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        triggerRef.current &&
        menuRef.current &&
        !triggerRef.current.contains(event.target as Node) &&
        !menuRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault();
        setIsOpen(true);
        setSelectedIndex(0);
      }
      return;
    }

    const enabledItems = items.filter((item) => !item.disabled);

    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setSelectedIndex(null);
        triggerRef.current?.focus();
        break;
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => {
          if (prev === null) return 0;
          const nextIndex = items.findIndex(
            (item, i) => i > prev && !item.disabled
          );
          return nextIndex === -1 ? prev : nextIndex;
        });
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => {
          if (prev === null) return 0;
          const prevIndex = items
            .map((item, i) => ({ item, i }))
            .reverse()
            .find(({ item, i }) => i < prev && !item.disabled)?.i;
          return prevIndex ?? prev;
        });
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (selectedIndex !== null && items[selectedIndex]?.onClick) {
          items[selectedIndex].onClick();
          setIsOpen(false);
        }
        break;
    }
  };

  const handleItemClick = (item: DropdownItemProps, index: number) => {
    if (item.disabled) return;
    item.onClick?.();
    setIsOpen(false);
  };

  const alignStyles = {
    start: 'left-0',
    end: 'right-0',
    center: 'left-1/2 -translate-x-1/2',
  };

  return (
    <DropdownContext.Provider value={{ isOpen, setIsOpen, selectedIndex, setSelectedIndex }}>
      <div className="relative" onKeyDown={handleKeyDown}>
        <div
          ref={triggerRef}
          tabIndex={0}
          role="button"
          aria-haspopup="menu"
          aria-expanded={isOpen}
          className="inline-flex"
          onClick={() => setIsOpen(!isOpen)}
        >
          {trigger}
        </div>

        {isOpen && (
          <div
            ref={menuRef}
            className={cn(
              'absolute z-50 mt-1 rounded-lg border border-border bg-surface shadow-lg',
              'py-1',
              'animate-in fade-in duration-200',
              alignStyles[align],
              className
            )}
            style={{ width, top: '100%' }}
            role="menu"
          >
            {items.map((item, index) => (
              <div
                key={item.value}
                role="menuitem"
                tabIndex={item.disabled ? -1 : 0}
                aria-disabled={item.disabled}
                className={cn(
                  'flex items-start gap-3 px-3 py-2 cursor-pointer transition-colors',
                  'focus:outline-none focus:bg-surface-2',
                  index === selectedIndex && 'bg-surface-2',
                  item.disabled && 'opacity-50 cursor-not-allowed pointer-events-none'
                )}
                onClick={() => handleItemClick(item, index)}
              >
                {item.icon && (
                  <span className="flex-shrink-0 text-text-secondary">
                    {item.icon}
                  </span>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text-primary truncate">{item.label}</p>
                  {item.description && (
                    <p className="text-xs text-text-secondary truncate">{item.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DropdownContext.Provider>
  );
};

DropdownMenu.displayName = 'DropdownMenu';

// ============================================================================
// DropdownTrigger Component
// ============================================================================

const DropdownTrigger = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>;
};

DropdownTrigger.displayName = 'DropdownTrigger';

// ============================================================================
// DropdownItem Component
// ============================================================================

const DropdownItem = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return <div className={className}>{children}</div>;
};

DropdownItem.displayName = 'DropdownItem';

export { DropdownMenu, DropdownTrigger, DropdownItem };

'use client';

import * as React from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

interface SectionPanelProps {
  title: string;
  description?: string;
  required?: boolean;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  accentColor?: 'cyan' | 'purple' | 'pink';
  children: React.ReactNode;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export const SectionPanel: React.FC<SectionPanelProps> = ({
  title,
  description,
  required,
  collapsible = false,
  defaultCollapsed = false,
  accentColor = 'cyan',
  children,
  className,
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(defaultCollapsed);

  const accentColors = {
    cyan: 'bg-accent-cyan',
    purple: 'bg-accent-purple',
    pink: 'bg-accent-pink',
  };

  return (
    <section
      className={cn(
        'relative bg-surface border border-border rounded-lg overflow-hidden',
        className
      )}
    >
      {/* Accent bar */}
      <div
        className={cn(
          'absolute left-0 top-0 bottom-0 w-0.5 rounded-l-lg',
          accentColors[accentColor]
        )}
      />

      {/* Header */}
      <div
        className={cn(
          'flex items-start justify-between gap-4 px-5 py-4',
          collapsible && 'cursor-pointer select-none'
        )}
        onClick={collapsible ? () => setIsCollapsed(!isCollapsed) : undefined}
      >
        <div className="flex-1 min-w-0 pl-1">
          <h3 className="text-base font-semibold text-text-primary flex items-center gap-2">
            {title}
            {required && (
              <span className="text-error text-sm">*</span>
            )}
          </h3>
          {description && (
            <p className="text-sm text-text-secondary mt-1">{description}</p>
          )}
        </div>

        {collapsible && (
          <ChevronDown
            className={cn(
              'w-5 h-5 text-text-muted transition-transform duration-200',
              isCollapsed && '-rotate-90'
            )}
          />
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          'px-5 pb-5 pl-6 transition-all duration-200',
          isCollapsed ? 'h-0 overflow-hidden p-0' : ''
        )}
      >
        {children}
      </div>
    </section>
  );
};

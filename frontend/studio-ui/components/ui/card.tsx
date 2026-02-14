'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export type CardStatus = 'running' | 'stopped' | 'error' | 'pending';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined' | 'interactive' | 'status';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  selected?: boolean;
  status?: CardStatus;
  hoverable?: boolean;
  compact?: boolean;
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

// ============================================================================
// Status Visual Config
// ============================================================================

const statusAccentColors: Record<CardStatus, string> = {
  running: 'bg-success',
  stopped: 'bg-text-muted',
  error: 'bg-error',
  pending: 'bg-warning',
};

// ============================================================================
// Card Component
// ============================================================================

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = 'default',
      padding = 'md',
      selected,
      status,
      hoverable,
      compact,
      children,
      ...props
    },
    ref
  ) => {
    const isInteractive = variant === 'interactive' || hoverable;
    const isStatusCard = status !== undefined;

    return (
      <div
        ref={ref}
        className={cn(
          'relative rounded-lg border border-border bg-surface',
          'transition-all duration-200 ease-out',

          // Padding
          {
            '': padding === 'none',
            'p-3': padding === 'sm',
            'p-4': padding === 'md',
            'p-6': padding === 'lg',
            'p-2': compact,
          },

          // Variants
          {
            '': variant === 'default',
            'shadow-md border-transparent': variant === 'elevated',
            'bg-transparent': variant === 'outlined',
          },

          // Interactive/Hoverable
          isInteractive && 'hover:border-border-strong hover:bg-surface-2 cursor-pointer hover:shadow-elevation-2',

          // Selected state with glow
          selected && 'border-accent-cyan shadow-glow-cyan-ring',

          // Status accent bar
          isStatusCard && 'border-l-[3px]',
          status === 'running' && 'border-l-success',
          status === 'stopped' && 'border-l-text-muted',
          status === 'error' && 'border-l-error',
          status === 'pending' && 'border-l-warning',

          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// ============================================================================
// CardHeader Component
// ============================================================================

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, title, description, action, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex items-start justify-between gap-4', className)}
        {...props}
      >
        <div className="flex-1 min-w-0">
          {title && (
            <h3 className="text-base font-semibold text-text-primary truncate">
              {title}
            </h3>
          )}
          {description && (
            <p className="text-sm text-text-secondary mt-1">{description}</p>
          )}
          {children}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

// ============================================================================
// CardContent Component
// ============================================================================

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('mt-4', className)} {...props} />
));

CardContent.displayName = 'CardContent';

// ============================================================================
// CardFooter Component
// ============================================================================

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'mt-4 pt-4 border-t border-border flex items-center gap-3',
        className
      )}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardContent, CardFooter };

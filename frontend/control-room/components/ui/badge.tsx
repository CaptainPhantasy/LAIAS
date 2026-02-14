'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  pulse?: boolean;
  dot?: boolean;
}

// ============================================================================
// Component
// ============================================================================

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  (
    {
      className,
      variant = 'default',
      pulse = false,
      dot = false,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium transition-all duration-200',

          // Variant styles
          {
            // Default
            'bg-surface border border-border text-text-primary':
              variant === 'default',

            // Success
            'bg-success/10 border border-success/20 text-success':
              variant === 'success',

            // Warning
            'bg-warning/10 border border-warning/20 text-warning':
              variant === 'warning',

            // Error
            'bg-error/10 border border-error/20 text-error':
              variant === 'error',

            // Info
            'bg-info/10 border border-info/20 text-info':
              variant === 'info',
          },

          // Pulse animation
          pulse && 'animate-pulse',

          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={cn(
              'w-1.5 h-1.5 rounded-full',

              // Dot color by variant
              {
                'bg-bg-primary': variant === 'default',
                'bg-success': variant === 'success',
                'bg-warning': variant === 'warning',
                'bg-error': variant === 'error',
                'bg-info': variant === 'info',
              }
            )}
          />
        )}
        {children}
      </div>
    );
  }
);

Badge.displayName = 'Badge';

export { Badge };

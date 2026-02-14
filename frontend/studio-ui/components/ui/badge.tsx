'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'success' | 'warning' | 'error' | 'info' | 'cyan' | 'purple';
  size?: 'sm' | 'md';
}

// ============================================================================
// Component
// ============================================================================

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'sm', ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center font-medium rounded-full',
          'transition-colors duration-150',

          // Size
          {
            'text-xs px-2 py-0.5': size === 'sm',
            'text-sm px-3 py-1': size === 'md',
          },

          // Variants
          {
            'bg-surface-2 text-text-secondary': variant === 'default',
            'bg-transparent border border-border text-text-secondary': variant === 'outline',
            'bg-success/20 text-success': variant === 'success',
            'bg-warning/20 text-warning': variant === 'warning',
            'bg-error/20 text-error': variant === 'error',
            'bg-info/20 text-info': variant === 'info',
            'bg-accent-cyan/20 text-accent-cyan': variant === 'cyan',
            'bg-accent-purple/20 text-accent-purple': variant === 'purple',
          },

          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';

export { Badge };

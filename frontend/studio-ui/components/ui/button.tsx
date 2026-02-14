'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'link';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  asChild?: boolean;
}

// ============================================================================
// Component
// ============================================================================

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      loading = false,
      fullWidth = false,
      iconLeft,
      iconRight,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center gap-2 font-medium',
          'rounded-lg transition-all duration-200 ease-out',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none disabled:grayscale-[0.5]',

          // Variant styles
          {
            // Primary - Cyan with glow
            'bg-accent-cyan text-bg-primary hover:shadow-glow-cyan hover:brightness-105 hover:scale-[1.02] active:scale-[0.98]':
              variant === 'primary',

            // Secondary - Purple outlined
            'bg-transparent border border-accent-purple text-accent-purple hover:bg-accent-purple/10 hover:shadow-glow-purple hover:scale-[1.02] active:scale-[0.98]':
              variant === 'secondary',

            // Outline - Subtle border
            'bg-transparent border border-border text-text-primary hover:border-border-strong hover:bg-surface hover:scale-[1.01] active:scale-[0.99]':
              variant === 'outline',

            // Ghost - No border
            'bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface':
              variant === 'ghost',

            // Destructive - Red
            'bg-error text-white hover:bg-error/90 hover:shadow-glow-error hover:scale-[1.02] active:scale-[0.98]':
              variant === 'destructive',

            // Link - Text only
            'bg-transparent text-accent-cyan underline-offset-4 hover:underline':
              variant === 'link',
          },

          // Size styles
          {
            'text-xs px-2.5 py-1.5': size === 'sm',
            'text-sm px-4 py-2': size === 'md',
            'text-base px-6 py-3': size === 'lg',
          },

          // Full width
          fullWidth && 'w-full',

          className
        )}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!loading && iconLeft}
        {children}
        {!loading && iconRight}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };

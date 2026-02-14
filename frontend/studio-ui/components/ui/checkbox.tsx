'use client';

import * as React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  description?: string;
}

// ============================================================================
// Component
// ============================================================================

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, description, checked, onChange, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id || generatedId;

    return (
      <div className="flex items-start gap-3">
        <div className="relative flex items-center justify-center">
          <input
            ref={ref}
            type="checkbox"
            id={inputId}
            checked={checked}
            onChange={onChange}
            className={cn(
              'peer appearance-none',
              'w-5 h-5 rounded border-2 border-border',
              'bg-bg-tertiary',
              'transition-all duration-150',
              'cursor-pointer',
              'checked:bg-accent-cyan checked:border-accent-cyan',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              className
            )}
            {...props}
          />
          <Check
            className={cn(
              'absolute w-3.5 h-3.5 text-bg-primary',
              'opacity-0 peer-checked:opacity-100',
              'transition-opacity duration-150',
              'pointer-events-none'
            )}
            strokeWidth={3}
          />
        </div>

        {(label || description) && (
          <div className="flex-1 min-w-0">
            {label && (
              <label
                htmlFor={inputId}
                className="text-sm font-medium text-text-primary cursor-pointer"
              >
                {label}
              </label>
            )}
            {description && (
              <p className="text-xs text-text-muted mt-0.5">{description}</p>
            )}
          </div>
        )}
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';

export { Checkbox };

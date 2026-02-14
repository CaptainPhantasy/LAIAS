'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Search, X } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface SearchInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  onValueChange?: (value: string) => void;
  showClearButton?: boolean;
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

// ============================================================================
// Component
// ============================================================================

const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  (
    {
      className,
      value: controlledValue,
      defaultValue = '',
      onValueChange,
      showClearButton = true,
      size = 'md',
      icon,
      disabled,
      ...props
    },
    ref
  ) => {
    const [uncontrolledValue, setUncontrolledValue] = React.useState(defaultValue);
    const isControlled = controlledValue !== undefined;
    const value = isControlled ? controlledValue : uncontrolledValue;
    const inputRef = React.useRef<HTMLInputElement>(null);

    // Handle both ref types
    React.useImperativeHandle(ref, () => inputRef.current!);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      if (!isControlled) {
        setUncontrolledValue(newValue);
      }
      onValueChange?.(newValue);
    };

    const handleClear = () => {
      if (!isControlled) {
        setUncontrolledValue('');
      }
      onValueChange?.('');
      inputRef.current?.focus();
    };

    const sizeStyles = {
      sm: 'h-8 pl-8 pr-7 text-sm',
      md: 'h-10 pl-9 pr-8 text-sm',
      lg: 'h-12 pl-10 pr-9 text-base',
    };

    const iconSizeStyles = {
      sm: 'w-3.5 h-3.5 left-2.5',
      md: 'w-4 h-4 left-3',
      lg: 'w-5 h-5 left-3.5',
    };

    const clearButtonSizeStyles = {
      sm: 'w-5 h-5 right-1.5',
      md: 'w-6 h-6 right-2',
      lg: 'w-7 h-7 right-2.5',
    };

    return (
      <div className="relative">
        {/* Search Icon */}
        <div
          className={cn(
            'absolute top-1/2 -translate-y-1/2 text-text-secondary pointer-events-none',
            iconSizeStyles[size]
          )}
        >
          {icon || <Search />}
        </div>

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={handleChange}
          disabled={disabled}
          className={cn(
            'w-full rounded-lg border border-border bg-surface text-text-primary placeholder:text-text-3',
            'transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-accent-cyan focus:ring-offset-2 focus:ring-offset-bg-primary focus:border-accent-cyan',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'pr-10', // Space for clear button
            sizeStyles[size],
            className
          )}
          {...props}
        />

        {/* Clear Button */}
        {showClearButton && value && (
          <button
            type="button"
            onClick={handleClear}
            disabled={disabled}
            className={cn(
              'absolute top-1/2 -translate-y-1/2 flex items-center justify-center',
              'rounded-md text-text-secondary hover:text-text-primary',
              'hover:bg-surface-2 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              clearButtonSizeStyles[size]
            )}
            aria-label="Clear search"
          >
            <X className="w-3 h-3" />
          </button>
        )}
      </div>
    );
  }
);

SearchInput.displayName = 'SearchInput';

export { SearchInput };

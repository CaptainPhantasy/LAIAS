'use client';

import * as React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

interface ToolTileProps {
  id: string;
  name: string;
  description: string;
  icon?: React.ReactNode;
  selected: boolean;
  disabled?: boolean;
  onSelect: (id: string, selected: boolean) => void;
}

// ============================================================================
// Component
// ============================================================================

export const ToolTile: React.FC<ToolTileProps> = ({
  id,
  name,
  description,
  icon,
  selected,
  disabled = false,
  onSelect,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(id, !selected);
    }
  };

  return (
    <button
      type="button"
      onClick={() => onSelect(id, !selected)}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      className={cn(
        'relative w-full p-4 rounded-lg',
        'text-left transition-all duration-200',
        'border-2',

        // Base state
        'bg-surface border-border',

        // Hover state
        !disabled && 'hover:border-border-strong hover:bg-surface-2',

        // Selected state
        selected && [
          'border-accent-cyan bg-accent-cyan/5',
          'shadow-[0_0_0_1px_rgba(45,226,255,0.3),0_0_20px_rgba(45,226,255,0.15)]',
        ],

        // Disabled state
        disabled && 'opacity-50 cursor-not-allowed',

        // Focus state
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary'
      )}
      role="checkbox"
      aria-checked={selected}
      aria-disabled={disabled}
    >
      {/* Selected indicator */}
      {selected && (
        <div
          className={cn(
            'absolute top-3 right-3',
            'w-5 h-5 rounded-full bg-accent-cyan',
            'flex items-center justify-center'
          )}
        >
          <Check className="w-3 h-3 text-bg-primary" strokeWidth={3} />
        </div>
      )}

      {/* Icon */}
      {icon && (
        <div
          className={cn(
            'w-10 h-10 rounded-lg mb-3',
            'flex items-center justify-center',
            'bg-bg-tertiary',
            selected ? 'text-accent-cyan' : 'text-text-muted'
          )}
        >
          {icon}
        </div>
      )}

      {/* Content */}
      <h4 className="text-sm font-semibold text-text-primary mb-1 pr-6">{name}</h4>
      <p className="text-xs text-text-secondary line-clamp-2">{description}</p>
    </button>
  );
};

'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

interface PromptSuggestion {
  id: string;
  label: string;
  prompt: string;
}

interface PromptSuggestionsProps {
  suggestions: PromptSuggestion[];
  onSelect: (prompt: string) => void;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export const PromptSuggestions: React.FC<PromptSuggestionsProps> = ({
  suggestions,
  onSelect,
  className,
}) => {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {suggestions.map((suggestion) => (
        <button
          key={suggestion.id}
          type="button"
          onClick={() => onSelect(suggestion.prompt)}
          className={cn(
            'px-3 py-1.5 rounded-full',
            'text-xs font-medium',
            'border border-accent-purple/50 text-accent-purple',
            'bg-transparent',
            'transition-all duration-150',
            'hover:bg-accent-purple/10 hover:border-accent-purple',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-purple focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary'
          )}
        >
          {suggestion.label}
        </button>
      ))}
    </div>
  );
};

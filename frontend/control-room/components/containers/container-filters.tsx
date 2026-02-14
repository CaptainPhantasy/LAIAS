'use client';

import * as React from 'react';
import { Search, X, Filter, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import type { ContainerStatus, ContainerFilters } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface ContainerFiltersProps {
  filters: ContainerFilters;
  onFilterChange: (filters: Partial<ContainerFilters>) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  className?: string;
}

// ============================================================================
// Constants
// ============================================================================

const STATUS_OPTIONS: Array<{ value: ContainerStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'running', label: 'Running' },
  { value: 'stopped', label: 'Stopped' },
  { value: 'paused', label: 'Paused' },
  { value: 'error', label: 'Error' },
];

// ============================================================================
// Component
// ============================================================================

export function ContainerFilters({
  filters,
  onFilterChange,
  onRefresh,
  isRefreshing = false,
  className,
}: ContainerFiltersProps) {
  return (
    <div className={cn('flex flex-wrap items-center gap-3', className)}>
      {/* Search */}
      <div className="relative flex-1 min-w-[200px] max-w-[300px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <input
          type="text"
          placeholder="Search containers..."
          value={filters.search}
          onChange={(e) => onFilterChange({ search: e.target.value })}
          className={cn(
            'w-full pl-9 pr-8 py-2 text-sm',
            'bg-surface border border-border rounded-lg',
            'text-text-primary placeholder:text-text-muted',
            'focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan',
            'transition-colors'
          )}
        />
        {filters.search && (
          <button
            onClick={() => onFilterChange({ search: '' })}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-surface-2 rounded"
          >
            <X className="w-3 h-3 text-text-muted" />
          </button>
        )}
      </div>

      {/* Status Filter */}
      <div className="flex items-center gap-1">
        <Filter className="w-4 h-4 text-text-muted" />
        <select
          value={filters.status}
          onChange={(e) => onFilterChange({ status: e.target.value as ContainerStatus | 'all' })}
          className={cn(
            'px-3 py-2 text-sm',
            'bg-surface border border-border rounded-lg',
            'text-text-primary',
            'focus:outline-none focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan',
            'cursor-pointer'
          )}
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Refresh */}
      {onRefresh && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          <RefreshCw className={cn('w-4 h-4', isRefreshing && 'animate-spin')} />
        </Button>
      )}
    </div>
  );
}

ContainerFilters.displayName = 'ContainerFilters';

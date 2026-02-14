'use client';

import * as React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { DashboardMetric } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface KPICardProps {
  metric: DashboardMetric;
  className?: string;
  compact?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function KPICard({ metric, className, compact = false }: KPICardProps) {
  const { label, value, unit, trend, trendValue, status } = metric;

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

  const statusColors: Record<string, string> = {
    success: 'text-success',
    warning: 'text-warning',
    error: 'text-error',
    neutral: 'text-text-primary',
  };

  const trendColors: Record<string, string> = {
    up: 'text-success',
    down: 'text-error',
    stable: 'text-text-muted',
  };

  return (
    <div
      className={cn(
        'bg-surface border border-border rounded-lg p-6',
        'transition-all duration-200 hover:shadow-md hover:border-border-strong',
        'shadow-sm',
        status === 'error' && 'border-error/30 bg-error/5',
        compact && 'p-4',
        className
      )}
    >
      <p className="text-sm font-medium text-text-secondary mb-2">{label}</p>

      <div className="flex items-baseline gap-1.5">
        <span
          className={cn(
            'text-3xl font-bold tracking-tight',
            statusColors[status],
            compact && 'text-2xl'
          )}
        >
          {value}
        </span>
        {unit && <span className="text-sm font-medium text-text-muted">{unit}</span>}
      </div>

      {(trend || trendValue) && (
        <div className={cn('flex items-center gap-1.5 mt-2', trendColors[trend || 'stable'])}>
          <TrendIcon className="w-4 h-4" />
          {trendValue && <span className="text-sm font-medium">{trendValue}</span>}
        </div>
      )}
    </div>
  );
}

KPICard.displayName = 'KPICard';

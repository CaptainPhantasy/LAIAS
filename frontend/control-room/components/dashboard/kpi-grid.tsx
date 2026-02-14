'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { KPICard } from './kpi-card';
import type { DashboardMetric } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface KPIGridProps {
  metrics: DashboardMetric[];
  columns?: 2 | 3 | 4;
  compact?: boolean;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function KPIGrid({ metrics, columns = 4, compact = false, className }: KPIGridProps) {
  const gridCols: Record<number, string> = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={cn('grid gap-6', gridCols[columns], className)}>
      {metrics.map((metric) => (
        <KPICard key={metric.id} metric={metric} compact={compact} />
      ))}
    </div>
  );
}

KPIGrid.displayName = 'KPIGrid';

'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { ContainerCard } from './container-card';
import type { ContainerInfo } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface ContainerGridProps {
  containers: ContainerInfo[];
  onAction?: (containerId: string, action: 'start' | 'stop' | 'restart' | 'remove' | 'logs' | 'metrics') => void;
  loadingId?: string | null;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function ContainerGrid({ containers, onAction, loadingId, className }: ContainerGridProps) {
  if (containers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="text-4xl mb-4">📦</div>
        <h3 className="text-lg font-medium text-text-primary mb-1">No Containers</h3>
        <p className="text-sm text-text-muted">
          Deploy agents from the Studio to see them here
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'grid gap-4',
        'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
        className
      )}
    >
      {containers.map((container) => (
        <ContainerCard
          key={container.container_id}
          container={container}
          isLoading={loadingId === container.container_id}
          onStart={() => onAction?.(container.container_id || '', 'start')}
          onStop={() => onAction?.(container.container_id || '', 'stop')}
          onRestart={() => onAction?.(container.container_id || '', 'restart')}
          onRemove={() => onAction?.(container.container_id || '', 'remove')}
          onViewLogs={() => onAction?.(container.container_id || '', 'logs')}
          onViewMetrics={() => onAction?.(container.container_id || '', 'metrics')}
        />
      ))}
    </div>
  );
}

ContainerGrid.displayName = 'ContainerGrid';

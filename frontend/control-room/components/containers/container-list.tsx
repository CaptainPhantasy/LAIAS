'use client';

import * as React from 'react';
import Link from 'next/link';
import { Play, Square, RefreshCw, Trash2, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/status';
import { formatUptime, formatPercent, truncateId } from '@/lib/formatters';
import type { ContainerInfo } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface ContainerListProps {
  containers: ContainerInfo[];
  onAction?: (containerId: string, action: 'start' | 'stop' | 'restart' | 'remove' | 'logs') => void;
  loadingId?: string | null;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function ContainerList({ containers, onAction, loadingId, className }: ContainerListProps) {
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
    <div className={cn('space-y-2', className)}>
      {/* Header */}
      <div className="grid grid-cols-12 gap-4 px-4 py-2 text-xs font-medium text-text-muted border-b border-border">
        <div className="col-span-4">Name</div>
        <div className="col-span-2">Status</div>
        <div className="col-span-2">CPU</div>
        <div className="col-span-2">Memory</div>
        <div className="col-span-2 text-right">Actions</div>
      </div>

      {/* Rows */}
      {containers.map((container) => {
        const isRunning = container.status === 'running';
        const isLoading = loadingId === container.container_id;
        const rawStatus = container.status || 'stopped';
        const badgeStatus: 'running' | 'stopped' | 'paused' | 'error' | 'pending' =
          rawStatus === 'exited' ? 'stopped' : rawStatus as 'running' | 'stopped' | 'paused' | 'error' | 'pending';

        return (
          <div
            key={container.container_id}
            className={cn(
              'grid grid-cols-12 gap-4 px-4 py-3 rounded-lg',
              'bg-surface border border-border',
              'hover:border-border-strong transition-colors',
              'items-center'
            )}
          >
            {/* Name */}
            <div className="col-span-4 min-w-0">
              <Link
                href={`/containers/${container.container_id}`}
                className="text-sm font-medium text-text-primary hover:text-accent-cyan truncate block"
              >
                {container.agent_name || container.name || 'Unknown'}
              </Link>
              <p className="text-xs text-text-muted">{truncateId(container.container_id || '')}</p>
            </div>

            {/* Status */}
            <div className="col-span-2">
              <StatusBadge status={badgeStatus} size="sm" />
            </div>

            {/* CPU */}
            <div className="col-span-2 text-sm">
              {isRunning && container.resource_usage ? (
                <span className={cn(
                  (container.resource_usage.cpu_percent || 0) > 80 ? 'text-warning' : 'text-text-primary'
                )}>
                  {formatPercent(container.resource_usage.cpu_percent || 0)}
                </span>
              ) : (
                <span className="text-text-muted">—</span>
              )}
            </div>

            {/* Memory */}
            <div className="col-span-2 text-sm text-text-primary">
              {isRunning && container.resource_usage ? (
                container.resource_usage.memory_usage
              ) : (
                <span className="text-text-muted">—</span>
              )}
            </div>

            {/* Actions */}
            <div className="col-span-2 flex items-center justify-end gap-1">
              {!isRunning ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onAction?.(container.container_id || '', 'start')}
                  disabled={isLoading}
                >
                  <Play className="w-4 h-4 text-success" />
                </Button>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onAction?.(container.container_id || '', 'stop')}
                  disabled={isLoading}
                >
                  <Square className="w-4 h-4 text-warning" />
                </Button>
              )}

              <Button
                variant="ghost"
                size="sm"
                onClick={() => onAction?.(container.container_id || '', 'logs')}
              >
                <FileText className="w-4 h-4" />
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => onAction?.(container.container_id || '', 'remove')}
                disabled={isLoading || isRunning}
              >
                <Trash2 className="w-4 h-4 text-error" />
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

ContainerList.displayName = 'ContainerList';

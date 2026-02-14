'use client';

import * as React from 'react';
import Link from 'next/link';
import { Play, Square, RefreshCw, Trash2, FileText, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/status';
import { formatUptime, formatPercent, formatBytes } from '@/lib/formatters';
import type { ContainerInfo, ResourceUsage, ContainerStatus } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface ContainerCardProps {
  container: ContainerInfo;
  onStart?: () => void;
  onStop?: () => void;
  onRestart?: () => void;
  onRemove?: () => void;
  onViewLogs?: () => void;
  onViewMetrics?: () => void;
  isLoading?: boolean;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function ContainerCard({
  container,
  onStart,
  onStop,
  onRestart,
  onRemove,
  onViewLogs,
  onViewMetrics,
  isLoading = false,
  className,
}: ContainerCardProps) {
  const rawStatus = container.status || 'stopped';
  // Map 'exited' to 'stopped' for StatusBadge compatibility
  const status: 'running' | 'stopped' | 'paused' | 'error' | 'pending' =
    rawStatus === 'exited' ? 'stopped' : rawStatus as 'running' | 'stopped' | 'paused' | 'error' | 'pending';
  const isRunning = rawStatus === 'running';
  const resourceUsage = container.resource_usage;

  return (
    <div
      className={cn(
        'bg-surface border border-border rounded-lg overflow-hidden',
        'transition-all duration-200',
        'hover:border-border-strong hover:shadow-md',
        isRunning && 'border-l-2 border-l-success',
        status === 'error' && 'border-l-2 border-l-error',
        className
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <Link
              href={`/containers/${container.container_id}`}
              className="text-base font-medium text-text-primary hover:text-accent-cyan truncate block"
            >
              {container.agent_name || container.name || 'Unknown Container'}
            </Link>
            <p className="text-xs text-text-muted mt-0.5">
              {container.container_id?.slice(0, 12)}
            </p>
          </div>
          <StatusBadge status={status} size="sm" />
        </div>
      </div>

      {/* Metrics */}
      {isRunning && resourceUsage && (
        <div className="px-4 py-3 bg-surface-2/50 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-text-muted">CPU</span>
            <p className={cn(
              'font-medium',
              (resourceUsage.cpu_percent || 0) > 80 ? 'text-warning' : 'text-text-primary'
            )}>
              {formatPercent(resourceUsage.cpu_percent || 0)}
            </p>
          </div>
          <div>
            <span className="text-text-muted">Memory</span>
            <p className="text-text-primary font-medium">
              {resourceUsage.memory_usage || formatBytes(0)}
            </p>
          </div>
        </div>
      )}

      {/* Uptime */}
      <div className="px-4 py-2 text-xs text-text-muted">
        {isRunning ? (
          <span>Uptime: {formatUptime(container.started_at)}</span>
        ) : (
          <span>Not running</span>
        )}
      </div>

      {/* Actions */}
      <div className="p-3 border-t border-border flex items-center justify-between">
        <div className="flex items-center gap-1">
          {!isRunning ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={onStart}
              disabled={isLoading}
              title="Start"
            >
              <Play className="w-4 h-4 text-success" />
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              onClick={onStop}
              disabled={isLoading}
              title="Stop"
            >
              <Square className="w-4 h-4 text-warning" />
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={onRestart}
            disabled={isLoading || !isRunning}
            title="Restart"
          >
            <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={onRemove}
            disabled={isLoading || isRunning}
            title="Remove"
          >
            <Trash2 className="w-4 h-4 text-error" />
          </Button>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={onViewLogs}
            title="View Logs"
          >
            <FileText className="w-4 h-4" />
          </Button>
          {isRunning && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onViewMetrics}
              title="View Metrics"
            >
              <Activity className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

ContainerCard.displayName = 'ContainerCard';

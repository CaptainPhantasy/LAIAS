'use client';

import * as React from 'react';
import Link from 'next/link';
import { Clock, ArrowRight, Box } from 'lucide-react';
import { cn } from '@/lib/utils';
import { StatusBadge } from '@/components/status';
import { formatRelativeTime, truncateId } from '@/lib/formatters';
import type { ContainerInfo } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface RecentDeploymentsProps {
  containers: ContainerInfo[];
  maxItems?: number;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function RecentDeployments({ containers, maxItems = 5, className }: RecentDeploymentsProps) {
  const recentContainers = containers
    .sort((a, b) => {
      const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
      const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
      return dateB - dateA;
    })
    .slice(0, maxItems);

  return (
    <div
      className={cn(
        'bg-surface border border-border rounded-lg p-6 shadow-sm',
        className
      )}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-text-primary">Recent Deployments</h3>
        <Link
          href="/containers"
          className="text-sm font-medium text-accent-cyan hover:text-accent-cyan/80 flex items-center gap-1 transition-colors"
        >
          View all
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {recentContainers.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="w-12 h-12 rounded-full bg-surface-2 flex items-center justify-center mb-3">
            <Box className="w-6 h-6 text-text-muted" />
          </div>
          <p className="text-sm font-medium text-text-primary mb-1">No containers deployed yet</p>
          <p className="text-xs text-text-muted">Generate and deploy agents from Studio UI</p>
        </div>
      ) : (
        <div className="space-y-2">
          {recentContainers.map((container) => {
            const rawStatus = container.status || 'stopped';
            const badgeStatus: 'running' | 'stopped' | 'paused' | 'error' | 'pending' =
              rawStatus === 'exited' ? 'stopped' : rawStatus as 'running' | 'stopped' | 'paused' | 'error' | 'pending';

            return (
            <Link
              key={container.container_id}
              href={`/containers/${container.container_id}`}
              className={cn(
                'flex items-center justify-between p-3 rounded-lg',
                'hover:bg-surface-2 transition-colors',
                'group'
              )}
            >
              <div className="flex items-center gap-3 min-w-0">
                <StatusBadge status={badgeStatus} size="sm" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-text-primary truncate">
                    {container.agent_name || container.name || 'Unknown'}
                  </p>
                  <p className="text-xs text-text-muted">
                    {truncateId(container.container_id || '')}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-text-muted">
                <Clock className="w-3 h-3" />
                <span>{formatRelativeTime(container.created_at || '')}</span>
              </div>
            </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

RecentDeployments.displayName = 'RecentDeployments';

'use client';

import * as React from 'react';
import Link from 'next/link';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/status';
import { QuickActions } from './quick-actions';
import { formatUptime, truncateId, formatDate } from '@/lib/formatters';
import type { ContainerInfo } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface ContainerDetailProps {
  container: ContainerInfo;
  onAction?: (action: 'start' | 'stop' | 'restart' | 'remove') => void;
  isLoading?: boolean;
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function ContainerDetail({
  container,
  onAction,
  isLoading = false,
  className,
}: ContainerDetailProps) {
  // Map 'exited' to 'stopped' for StatusBadge compatibility
  const rawStatus = container.status || 'stopped';
  const status: 'running' | 'stopped' | 'paused' | 'error' | 'pending' =
    rawStatus === 'exited' ? 'stopped' : rawStatus as 'running' | 'stopped' | 'paused' | 'error' | 'pending';

  return (
    <div className={cn('space-y-6', className)}>
      {/* Back link */}
      <Link
        href="/containers"
        className="inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Containers
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">
            {container.agent_name || container.name || 'Container'}
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <StatusBadge status={status} />
            <span className="text-sm text-text-muted font-mono">
              {truncateId(container.container_id || '')}
            </span>
          </div>
        </div>

        <QuickActions
          status={rawStatus}
          onAction={onAction}
          isLoading={isLoading}
        />
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <InfoCard label="Agent ID" value={truncateId(container.agent_id || '', 8)} />
        <InfoCard label="Created" value={formatDate(container.created_at || '')} />
        <InfoCard
          label="Uptime"
          value={rawStatus === 'running' ? formatUptime(container.started_at) : '—'}
        />
        <InfoCard label="Image" value={container.image?.split(':')[0] || 'laias/agent-runner'} />
      </div>

      {/* Ports */}
      {container.ports && container.ports.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-4">
          <h3 className="text-sm font-medium text-text-secondary mb-3">Ports</h3>
          <div className="flex flex-wrap gap-2">
            {container.ports.map((port, i) => (
              <span
                key={i}
                className="px-2 py-1 bg-surface-2 rounded text-sm text-text-primary font-mono"
              >
                {port.host_port}:{port.container_port}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Helper component
function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-3">
      <p className="text-xs text-text-muted mb-1">{label}</p>
      <p className="text-sm text-text-primary font-medium truncate">{value}</p>
    </div>
  );
}

ContainerDetail.displayName = 'ContainerDetail';

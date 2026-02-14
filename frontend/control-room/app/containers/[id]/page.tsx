'use client';

import { use, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ContainerDetail } from '@/components/containers';
import { MetricsPanel } from '@/components/metrics';
import { useContainers, useContainerActions, useMetrics } from '@/hooks';
import { getContainer } from '@/lib/api';

// ============================================================================
// Container Detail Page
// ============================================================================

export default function ContainerDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [actionLoading, setActionLoading] = useState(false);

  // Get container from list
  const { containers, refetch } = useContainers({ autoRefresh: true });
  const container = containers.find((c) => c.container_id === id);

  // Metrics for running containers
  const { metrics, history } = useMetrics({
    containerId: id,
    autoRefresh: container?.status === 'running',
  });

  // Container actions
  const { start, stop, restart, remove } = useContainerActions();

  const handleAction = useCallback(
    async (action: 'start' | 'stop' | 'restart' | 'remove') => {
      setActionLoading(true);
      try {
        switch (action) {
          case 'start':
            await start(id);
            break;
          case 'stop':
            await stop(id);
            break;
          case 'restart':
            await restart(id);
            break;
          case 'remove':
            if (confirm('Are you sure you want to remove this container?')) {
              await remove(id);
              router.push('/containers');
              return;
            }
            break;
        }
        refetch();
      } catch (error) {
        console.error(`Failed to ${action} container:`, error);
      } finally {
        setActionLoading(false);
      }
    },
    [id, start, stop, restart, remove, refetch, router]
  );

  if (!container) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-lg text-text-primary">Container not found</p>
          <p className="text-sm text-text-muted mt-1">
            The container may have been removed
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Container Header & Info */}
      <ContainerDetail
        container={container}
        onAction={handleAction}
        isLoading={actionLoading}
      />

      {/* Metrics Section (for running containers) */}
      {container.status === 'running' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">Resource Metrics</h2>
          <MetricsPanel
            containerId={id}
            showCPU={true}
            showMemory={true}
            showNetwork={true}
          />
        </div>
      )}
    </div>
  );
}

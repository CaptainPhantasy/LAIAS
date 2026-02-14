'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ContainerGrid, ContainerFilters } from '@/components/containers';
import { useContainers, useContainerActions } from '@/hooks';
import type { ContainerFilters as Filters } from '@/types';

// ============================================================================
// Containers Page
// ============================================================================

export default function ContainersPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<Filters>({
    search: '',
    status: 'all',
  });

  const { containers, isLoading, error, refetch, isRefetching } = useContainers({
    autoRefresh: true,
    status: filters.status === 'all' ? undefined : filters.status,
  });

  const { start, stop, restart, remove, loading: actionLoading } = useContainerActions();

  // Handle filter changes
  const handleFilterChange = useCallback((newFilters: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  }, []);

  // Filter containers by search
  const filteredContainers = containers.filter((container) => {
    if (!filters.search) return true;
    const query = filters.search.toLowerCase();
    return (
      (container.name?.toLowerCase().includes(query)) ||
      (container.agent_name?.toLowerCase().includes(query)) ||
      (container.container_id?.toLowerCase().includes(query))
    );
  });

  // Handle container actions
  const handleAction = useCallback(
    async (containerId: string, action: 'start' | 'stop' | 'restart' | 'remove' | 'logs' | 'metrics') => {
      try {
        switch (action) {
          case 'start':
            await start(containerId);
            break;
          case 'stop':
            await stop(containerId);
            break;
          case 'restart':
            await restart(containerId);
            break;
          case 'remove':
            if (confirm('Are you sure you want to remove this container?')) {
              await remove(containerId);
            }
            break;
          case 'logs':
            router.push(`/containers/${containerId}/logs`);
            break;
          case 'metrics':
            router.push(`/containers/${containerId}`);
            break;
        }
        // Refetch after action
        refetch();
      } catch (error) {
        console.error(`Failed to ${action} container:`, error);
      }
    },
    [start, stop, restart, remove, refetch, router]
  );

  // Get loading ID
  const loadingId = Object.entries(actionLoading).find(([_, v]) => v)?.[0] || null;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">Containers</h1>
          <p className="text-text-secondary mt-1">
            Manage your deployed AI agent containers
          </p>
        </div>
      </div>

      {/* Filters */}
      <ContainerFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        onRefresh={refetch}
        isRefreshing={isRefetching}
      />

      {/* Container Grid */}
      {error ? (
        <div className="flex items-center justify-center min-h-[200px] text-error">
          <p>Failed to load containers: {error}</p>
        </div>
      ) : (
        <ContainerGrid
          containers={filteredContainers}
          onAction={handleAction}
          loadingId={loadingId}
        />
      )}
    </div>
  );
}

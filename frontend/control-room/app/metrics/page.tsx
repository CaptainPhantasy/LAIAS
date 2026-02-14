'use client';

import { Activity, Cpu, HardDrive, Network } from 'lucide-react';
import { useContainers } from '@/hooks';

// ============================================================================
// Metrics Page
// ============================================================================

export default function MetricsPage() {
  const { containers, isLoading } = useContainers({ autoRefresh: true });

  // Calculate aggregate metrics
  const runningContainers = containers.filter((c) => c.status === 'running');

  const totalCpu = runningContainers.reduce(
    (sum, c) => sum + (c.resource_usage?.cpu_percent || 0),
    0
  );

  const avgCpu = runningContainers.length > 0 ? totalCpu / runningContainers.length : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">System Metrics</h1>
        <p className="text-text-secondary mt-1">
          Aggregate resource usage across all containers
        </p>
      </div>

      {/* Aggregate Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<Activity className="w-5 h-5" />}
          label="Running Containers"
          value={runningContainers.length}
          total={containers.length}
        />
        <MetricCard
          icon={<Cpu className="w-5 h-5" />}
          label="Avg CPU Usage"
          value={`${avgCpu.toFixed(1)}%`}
          status={avgCpu > 80 ? 'warning' : 'normal'}
        />
        <MetricCard
          icon={<HardDrive className="w-5 h-5" />}
          label="Total Containers"
          value={containers.length}
        />
        <MetricCard
          icon={<Network className="w-5 h-5" />}
          label="Error Containers"
          value={containers.filter((c) => c.status === 'error').length}
          status="error"
        />
      </div>

      {/* Running Containers List */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <h2 className="text-lg font-medium text-text-primary mb-4">Running Containers</h2>

        {runningContainers.length === 0 ? (
          <div className="text-center py-8 text-text-muted">
            No running containers
          </div>
        ) : (
          <div className="space-y-3">
            {runningContainers.map((container) => (
              <div
                key={container.container_id}
                className="flex items-center justify-between p-3 bg-surface-2 rounded-lg"
              >
                <div>
                  <p className="font-medium text-text-primary">
                    {container.agent_name || container.name}
                  </p>
                  <p className="text-xs text-text-muted font-mono">
                    {container.container_id?.slice(0, 12)}
                  </p>
                </div>

                <div className="flex items-center gap-6 text-sm">
                  <div>
                    <span className="text-text-muted">CPU:</span>{' '}
                    <span
                      className={
                        (container.resource_usage?.cpu_percent || 0) > 80
                          ? 'text-warning'
                          : 'text-text-primary'
                      }
                    >
                      {container.resource_usage?.cpu_percent?.toFixed(1) || 0}%
                    </span>
                  </div>
                  <div>
                    <span className="text-text-muted">Memory:</span>{' '}
                    <span className="text-text-primary">
                      {container.resource_usage?.memory_usage || '—'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Helper component
function MetricCard({
  icon,
  label,
  value,
  total,
  status = 'normal',
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  total?: number;
  status?: 'normal' | 'warning' | 'error';
}) {
  const statusColors = {
    normal: 'text-text-primary',
    warning: 'text-warning',
    error: 'text-error',
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="flex items-center gap-2 text-text-muted mb-2">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className={`text-2xl font-semibold ${statusColors[status]}`}>
          {value}
        </span>
        {total !== undefined && (
          <span className="text-text-muted text-sm">/ {total}</span>
        )}
      </div>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { Activity, Box, Cpu, HardDrive } from 'lucide-react';
import { KPIGrid, SystemStatus, RecentDeployments } from '@/components/dashboard';
import { useContainers } from '@/hooks';
import { healthCheck } from '@/lib/api';
import type { DashboardMetric, ContainerInfo } from '@/types';
import type { HealthResponse } from '../../shared/types';

// ============================================================================
// Dashboard Page
// ============================================================================

export default function DashboardPage() {
  const { containers, isLoading, refetch } = useContainers({ autoRefresh: true });
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Fetch health status
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await healthCheck();
        setHealth(response);
      } catch (error) {
        console.error('Failed to fetch health:', error);
      } finally {
        setHealthLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Calculate KPI metrics
  const metrics: DashboardMetric[] = [
    {
      id: 'total-containers',
      label: 'Total Containers',
      value: containers.length,
      status: 'neutral',
    },
    {
      id: 'running-containers',
      label: 'Running',
      value: containers.filter((c) => c.status === 'running').length,
      status: 'success',
    },
    {
      id: 'stopped-containers',
      label: 'Stopped',
      value: containers.filter((c) => c.status === 'stopped' || c.status === 'exited').length,
      status: 'warning',
    },
    {
      id: 'error-containers',
      label: 'Errors',
      value: containers.filter((c) => c.status === 'error').length,
      status: containers.filter((c) => c.status === 'error').length > 0 ? 'error' : 'neutral',
    },
  ];

  // System services status
  const services = health?.checks
    ? [
        {
          name: 'Database',
          status: health.checks.database?.status || 'unhealthy',
          latency: health.checks.database?.latency_ms,
        },
        {
          name: 'Redis',
          status: health.checks.redis?.status || 'unhealthy',
          latency: health.checks.redis?.latency_ms,
        },
        {
          name: 'LLM Provider',
          status: health.checks.llm_provider?.status || 'unhealthy',
          latency: health.checks.llm_provider?.latency_ms,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Dashboard</h1>
        <p className="text-text-secondary mt-1">
          Overview of your AI agent containers
        </p>
      </div>

      {/* KPI Cards */}
      <KPIGrid metrics={metrics} columns={4} />

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Status */}
        <SystemStatus services={services} />

        {/* Recent Deployments */}
        <RecentDeployments containers={containers} maxItems={5} />
      </div>

      {/* System Metrics */}
      {health?.metrics && (
        <div className="bg-surface border border-border rounded-lg p-6 shadow-sm">
          <h3 className="text-base font-semibold text-text-primary mb-4">System Metrics</h3>
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center py-2">
              <p className="text-3xl font-bold text-text-primary tracking-tight">
                {health.metrics.total_agents || 0}
              </p>
              <p className="text-sm font-medium text-text-muted mt-1">Total Agents</p>
            </div>
            <div className="text-center py-2">
              <p className="text-3xl font-bold text-success tracking-tight">
                {health.metrics.cache_hits || 0}
              </p>
              <p className="text-sm font-medium text-text-muted mt-1">Cache Hits</p>
            </div>
            <div className="text-center py-2">
              <p className="text-3xl font-bold text-text-primary tracking-tight">
                {health.metrics.cache_misses || 0}
              </p>
              <p className="text-sm font-medium text-text-muted mt-1">Cache Misses</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

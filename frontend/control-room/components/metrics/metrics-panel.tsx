/**
 * Metrics Panel Component
 * Container for multiple metrics charts with loading state
 */

'use client';

import { useMetrics } from '../../hooks/use-metrics';
import { CPUChart } from './cpu-chart';
import { MemoryChart } from './memory-chart';
import { NetworkChart } from './network-chart';
import { cn } from '../../lib/utils';

export interface MetricsPanelProps {
  /** Container ID to fetch metrics for */
  containerId: string;
  /** Whether to show CPU chart */
  showCPU?: boolean;
  /** Whether to show Memory chart */
  showMemory?: boolean;
  /** Whether to show Network chart */
  showNetwork?: boolean;
  /** Maximum data points to display */
  maxDataPoints?: number;
  /** Polling interval in milliseconds */
  pollingInterval?: number;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Loading skeleton for metrics panel
 */
function MetricsSkeleton() {
  return (
    <div className="space-y-4">
      {/* CPU skeleton */}
      <div className="h-[140px] bg-surface-2 rounded-lg animate-pulse" />
      {/* Memory skeleton */}
      <div className="h-[140px] bg-surface-2 rounded-lg animate-pulse" />
      {/* Network skeleton */}
      <div className="h-[140px] bg-surface-2 rounded-lg animate-pulse" />
    </div>
  );
}

/**
 * Error state display
 */
function MetricsError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="glass-surface rounded-lg p-6 border border-border">
      <div className="flex flex-col items-center justify-center gap-3 text-center">
        <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center">
           <svg
             className="w-6 h-6 text-error"
             fill="none"
             stroke="currentColor"
             viewBox="0 0 24 24"
             aria-label="Error icon"
           >
             <title>Error</title>
             <path
               strokeLinecap="round"
               strokeLinejoin="round"
               strokeWidth={2}
               d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
             />
           </svg>
        </div>
        <div>
          <h3 className="text-text font-semibold mb-1">Metrics Unavailable</h3>
          <p className="text-text-3 text-sm">{error}</p>
        </div>
         <button
           onClick={onRetry}
           className="px-4 py-2 bg-surface-2 hover:bg-surface-3 text-text rounded-lg text-sm transition-colors border border-border"
           type="button"
         >
           Retry
         </button>
      </div>
    </div>
  );
}

/**
 * Metrics panel container with multiple charts
 * - Displays CPU, Memory, and Network charts
 * - Shows loading skeleton while fetching
 * - Shows error state on failure
 * - Grid layout for responsive display
 */
export function MetricsPanel({
  containerId,
  showCPU = true,
  showMemory = true,
  showNetwork = true,
  maxDataPoints = 60,
  pollingInterval = 5000,
  className = '',
}: MetricsPanelProps) {
  const metrics = useMetrics({
    containerId,
    autoRefresh: true,
    refreshInterval: pollingInterval,
  });

  // Show skeleton on initial load
  if (metrics.isLoading && !metrics.metrics) {
    return <MetricsSkeleton />;
  }

   // Show error state
  if (metrics.error && !metrics.metrics) {
    return <MetricsError error={metrics.error} onRetry={metrics.refetch} />;
  }

  // Determine grid columns based on visible charts
  const visibleChartCount = [showCPU, showMemory, showNetwork].filter(Boolean).length;
  const gridCols = visibleChartCount === 1 ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2';

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with refresh button */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Container Metrics</h2>
         <button
           onClick={metrics.refetch}
           disabled={metrics.isLoading}
           className={cn(
             'p-2 rounded-lg transition-colors',
             'hover:bg-surface-2',
             'disabled:opacity-50 disabled:cursor-not-allowed'
           )}
           title="Refresh metrics"
           type="button"
         >
           <svg
             className={cn('w-4 h-4 text-text-2', metrics.isLoading && 'animate-spin')}
             fill="none"
             stroke="currentColor"
             viewBox="0 0 24 24"
             aria-label="Refresh icon"
           >
             <title>Refresh</title>
             <path
               strokeLinecap="round"
               strokeLinejoin="round"
               strokeWidth={2}
               d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
             />
           </svg>
        </button>
      </div>

      {/* Charts grid */}
      <div className={cn('grid gap-4', gridCols)}>
        {/* CPU Chart */}
        {showCPU && (
          <div className="glass-surface rounded-lg p-4 border border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-text-2">CPU Usage</h3>
          {metrics.metrics?.cpu?.percent !== undefined && (
            <span
              className={cn(
                'text-xs px-2 py-1 rounded-full',
                metrics.metrics.cpu.percent >= 90
                  ? 'bg-error/10 text-error'
                  : metrics.metrics.cpu.percent >= 70
                  ? 'bg-warning/10 text-warning'
                  : 'bg-success/10 text-success'
              )}
            >
              {metrics.metrics.cpu.percent.toFixed(1)}%
            </span>
          )}
            </div>
            <CPUChart data={metrics.history?.cpu || []} height={140} showLegend={false} />
          </div>
        )}

        {/* Memory Chart */}
        {showMemory && (
          <div className="glass-surface rounded-lg p-4 border border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-text-2">Memory Usage</h3>
          {metrics.metrics?.memory?.usage_bytes !== undefined && (
            <span
              className={cn(
                'text-xs px-2 py-1 rounded-full',
                metrics.metrics.memory.percent && metrics.metrics.memory.percent >= 90
                  ? 'bg-error/10 text-error'
                  : metrics.metrics.memory.percent && metrics.metrics.memory.percent >= 70
                  ? 'bg-warning/10 text-warning'
                  : 'bg-success/10 text-success'
              )}
            >
              {metrics.metrics.memory.percent?.toFixed(1) ?? 'N/A'}%
            </span>
          )}
            </div>
          <MemoryChart
            data={metrics.history?.memory || []}
            limitBytes={metrics.metrics?.memory?.limit_bytes}
            height={140}
            showLegend={false}
          />
          </div>
        )}

        {/* Network Chart - spans full width if all charts shown */}
        {showNetwork && (
          <div
            className={cn(
              'glass-surface rounded-lg p-4 border border-border',
              showCPU && showMemory ? 'lg:col-span-2' : ''
            )}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-text-2">Network Traffic</h3>
          <div className="flex items-center gap-3 text-xs text-text-3">
            <span className="flex items-center gap-1">
              <span className="w-2 h-1.5 rounded-full bg-[var(--accent-cyan)]" />
              RX: {metrics.metrics?.network?.rx_bytes
                ? `${(metrics.metrics.network.rx_bytes / 1024 / 1024).toFixed(1)} MB`
                : 'N/A'}
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-1.5 rounded-full bg-[var(--accent-pink)]" />
              TX: {metrics.metrics?.network?.tx_bytes
                ? `${(metrics.metrics.network.tx_bytes / 1024 / 1024).toFixed(1)} MB`
                : 'N/A'}
            </span>
          </div>
            </div>
            <NetworkChart
              rxData={metrics.history?.network.rx || []}
              txData={metrics.history?.network.tx || []}
              height={140}
              showLegend={true}
            />
          </div>
        )}
      </div>

      {/* Last updated timestamp */}
      {metrics.metrics?.timestamp && (
        <div className="text-xs text-text-3 text-center">
          Last updated: {new Date(metrics.metrics.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
}

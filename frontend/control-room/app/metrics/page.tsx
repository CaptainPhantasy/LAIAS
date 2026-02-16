'use client';

import { Activity, Cpu, HardDrive, Network, DollarSign, TrendingUp, BarChart3, Zap } from 'lucide-react';
import { useContainers } from '@/hooks';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useEffect, useState } from 'react';

// ============================================================================
// Types
// ============================================================================

interface UsageDataPoint {
  date: string;
  api_calls: number;
  tokens_used: number;
  cost_usd: number;
}

interface UsageStats {
  period_days: number;
  total_api_calls: number;
  total_tokens_used: number;
  total_cost_usd: number;
  cost_by_provider: Record<string, number>;
  tokens_by_provider: Record<string, { input: number; output: number }>;
  api_calls_by_endpoint: Record<string, number>;
  daily_timeseries: UsageDataPoint[];
}

interface DeploymentDataPoint {
  date: string;
  total: number;
  successful: number;
  failed: number;
  success_rate: number;
}

interface DeploymentStats {
  period_days: number;
  total_deployments: number;
  successful_deployments: number;
  failed_deployments: number;
  success_rate: number;
  deployments_by_status: Record<string, number>;
  daily_timeseries: DeploymentDataPoint[];
}

interface PerformanceDataPoint {
  date: string;
  avg_response_time_ms: number;
  request_count: number;
}

interface PerformanceMetrics {
  period_days: number;
  avg_response_time_ms: number;
  p50_response_time_ms: number;
  p95_response_time_ms: number;
  p99_response_time_ms: number;
  total_requests: number;
  daily_timeseries: PerformanceDataPoint[];
}

interface AnalyticsData {
  usage: UsageStats;
  deployments: DeploymentStats;
  performance: PerformanceMetrics;
}

// ============================================================================
// Metrics Page
// ============================================================================

export default function MetricsPage() {
  const { containers, isLoading } = useContainers({ autoRefresh: true });
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);

  // Calculate aggregate metrics
  const runningContainers = containers.filter((c) => c.status === 'running');
  const totalCpu = runningContainers.reduce(
    (sum, c) => sum + (c.resource_usage?.cpu_percent || 0),
    0
  );
  const avgCpu = runningContainers.length > 0 ? totalCpu / runningContainers.length : 0;

  // Fetch analytics data
  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setAnalyticsLoading(true);
        const response = await fetch(
          `http://localhost:8002/api/analytics?days=${timeRange}`
        );
        if (response.ok) {
          const data = await response.json();
          setAnalytics(data);
        }
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      } finally {
        setAnalyticsLoading(false);
      }
    };

    fetchAnalytics();
  }, [timeRange]);

  // Prepare chart data
  const costByProviderData = analytics
    ? Object.entries(analytics.usage.cost_by_provider).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const tokensByProviderData = analytics
    ? Object.entries(analytics.usage.tokens_by_provider).map(([name, tokens]) => ({
        name,
        input: tokens.input,
        output: tokens.output,
      }))
    : [];

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">System Metrics</h1>
          <p className="text-text-secondary mt-1">
            Aggregate resource usage and analytics across all containers
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
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

      {/* Analytics Cards */}
      {!analyticsLoading && analytics && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <AnalyticsMetricCard
              icon={<BarChart3 className="w-5 h-5 text-blue-500" />}
              label="Total API Calls"
              value={analytics.usage.total_api_calls.toLocaleString()}
              subtitle={`Last ${analytics.usage.period_days} days`}
            />
            <AnalyticsMetricCard
              icon={<DollarSign className="w-5 h-5 text-green-500" />}
              label="Total Cost"
              value={`$${analytics.usage.total_cost_usd.toFixed(2)}`}
              subtitle={`Token usage`}
            />
            <AnalyticsMetricCard
              icon={<TrendingUp className="w-5 h-5 text-purple-500" />}
              label="Deployments"
              value={analytics.deployments.total_deployments.toString()}
              subtitle={`${analytics.deployments.success_rate.toFixed(1)}% success`}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Usage Over Time */}
            <div className="bg-surface border border-border rounded-lg p-4">
              <h3 className="text-lg font-medium text-text-primary mb-4">
                API Calls Over Time
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={analytics.usage.daily_timeseries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="date"
                    stroke="#888"
                    tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: '8px' }}
                    labelFormatter={(v) => new Date(v).toLocaleDateString()}
                  />
                  <Area
                    type="monotone"
                    dataKey="api_calls"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Token Usage Trend */}
            <div className="bg-surface border border-border rounded-lg p-4">
              <h3 className="text-lg font-medium text-text-primary mb-4">
                Token Usage Trend
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={analytics.usage.daily_timeseries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="date"
                    stroke="#888"
                    tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis stroke="#888" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: '8px' }}
                    labelFormatter={(v) => new Date(v).toLocaleDateString()}
                    formatter={(value: number) => [value.toLocaleString(), 'tokens']}
                  />
                  <Line
                    type="monotone"
                    dataKey="tokens_used"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Cost Breakdown by Provider */}
            <div className="bg-surface border border-border rounded-lg p-4">
              <h3 className="text-lg font-medium text-text-primary mb-4">
                Cost by Provider
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={costByProviderData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {costByProviderData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: '8px' }}
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'cost']}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Deployment Success Rate */}
            <div className="bg-surface border border-border rounded-lg p-4">
              <h3 className="text-lg font-medium text-text-primary mb-4">
                Deployment Success Rate
              </h3>
              <div className="flex items-center justify-center h-[250px]">
                <div className="relative w-48 h-48">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="96"
                      cy="96"
                      r="88"
                      fill="none"
                      stroke="#333"
                      strokeWidth="16"
                    />
                    <circle
                      cx="96"
                      cy="96"
                      r="88"
                      fill="none"
                      stroke={analytics.deployments.success_rate >= 90 ? '#10b981' : analytics.deployments.success_rate >= 70 ? '#f59e0b' : '#ef4444'}
                      strokeWidth="16"
                      strokeDasharray={`${2 * Math.PI * 88}`}
                      strokeDashoffset={`${2 * Math.PI * 88 * (1 - analytics.deployments.success_rate / 100)}`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <span className={`text-4xl font-bold ${
                        analytics.deployments.success_rate >= 90 ? 'text-green-500' :
                        analytics.deployments.success_rate >= 70 ? 'text-yellow-500' :
                        'text-red-500'
                      }`}>
                        {analytics.deployments.success_rate.toFixed(1)}%
                      </span>
                      <p className="text-text-muted text-sm">Success</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Deployment Volume */}
            <div className="bg-surface border border-border rounded-lg p-4">
              <h3 className="text-lg font-medium text-text-primary mb-4">
                Deployment Volume
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={analytics.deployments.daily_timeseries}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="date"
                    stroke="#888"
                    tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: '8px' }}
                    labelFormatter={(v) => new Date(v).toLocaleDateString()}
                  />
                  <Legend />
                  <Bar dataKey="successful" stackId="a" fill="#10b981" name="Successful" />
                  <Bar dataKey="failed" stackId="a" fill="#ef4444" name="Failed" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Performance Metrics */}
            <div className="bg-surface border border-border rounded-lg p-4">
              <h3 className="text-lg font-medium text-text-primary mb-4">
                Response Time Percentiles
              </h3>
              <div className="space-y-4">
                <PercentileBar label="P50" value={analytics.performance.p50_response_time_ms} max={analytics.performance.p99_response_time_ms * 1.2} color="#3b82f6" />
                <PercentileBar label="P95" value={analytics.performance.p95_response_time_ms} max={analytics.performance.p99_response_time_ms * 1.2} color="#f59e0b" />
                <PercentileBar label="P99" value={analytics.performance.p99_response_time_ms} max={analytics.performance.p99_response_time_ms * 1.2} color="#ef4444" />
                <div className="pt-2 border-t border-border">
                  <p className="text-text-muted text-sm">
                    Avg: <span className="text-text-primary font-medium">{analytics.performance.avg_response_time_ms.toFixed(2)}ms</span>
                    {' '}| Total requests: <span className="text-text-primary font-medium">{analytics.performance.total_requests.toLocaleString()}</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Token Breakdown by Provider */}
          {tokensByProviderData.length > 0 && (
            <div className="bg-surface border border-border rounded-lg p-4">
              <h3 className="text-lg font-medium text-text-primary mb-4">
                Token Breakdown by Provider
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={tokensByProviderData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="name" stroke="#888" />
                  <YAxis stroke="#888" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: '8px' }}
                    formatter={(value: number) => [value.toLocaleString(), 'tokens']}
                  />
                  <Legend />
                  <Bar dataKey="input" fill="#3b82f6" name="Input Tokens" />
                  <Bar dataKey="output" fill="#10b981" name="Output Tokens" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}

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

// ============================================================================
// Helper Components
// ============================================================================

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

function AnalyticsMetricCard({
  icon,
  label,
  value,
  subtitle,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtitle?: string;
}) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-text-muted">{label}</span>
        {icon}
      </div>
      <div className="text-2xl font-semibold text-text-primary">{value}</div>
      {subtitle && (
        <div className="text-xs text-text-muted mt-1">{subtitle}</div>
      )}
    </div>
  );
}

function PercentileBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-text-muted">{label}</span>
        <span className="text-text-primary">{value.toFixed(2)}ms</span>
      </div>
      <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${percentage}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

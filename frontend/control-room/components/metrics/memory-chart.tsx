/**
 * Memory Chart Component
 * Area chart for memory usage over time
 */

'use client';

import {
  ResponsiveContainer,
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { formatBytes } from '../../lib/formatters';
import type { MetricDataPoint } from '../../types';

export interface MemoryChartProps {
  /** Metric data points (bytes) */
  data: MetricDataPoint[];
  /** Optional limit line to display */
  limitBytes?: number;
  /** Chart height in pixels */
  height?: number;
  /** Whether to show legend */
  showLegend?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Formatted data point for Recharts
 */
interface ChartDataPoint {
  time: string;
  value: number;
}

/**
 * Custom dark theme tooltip for memory chart
 */
function MemoryCustomTooltip({
  active,
  payload,
  limitBytes,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  limitBytes?: number;
}) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const value = payload[0].value;
  const percent = limitBytes ? (value / limitBytes) * 100 : null;
  const status = percent
    ? percent >= 90
      ? 'critical'
      : percent >= 70
      ? 'warning'
      : 'ok'
    : null;

  const statusColor =
    status === 'critical'
      ? 'var(--error)'
      : status === 'warning'
      ? 'var(--warning)'
      : 'var(--success)';

  return (
    <div className="glass-surface rounded-lg px-3 py-2 border border-border">
      <div className="text-xs text-text-3 mb-1">Memory Usage</div>
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold text-text">
          {formatBytes(value)}
        </span>
        {status && (
          <span
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: statusColor }}
          />
        )}
      </div>
      {percent !== null && (
        <div className="text-xs text-text-3 mt-1">{percent.toFixed(1)}%</div>
      )}
    </div>
  );
}

/**
 * Area chart for memory usage in bytes
 * - Y-axis: formatted bytes
 * - X-axis: time
 * - Purple gradient fill
 * - Optional limit line
 */
export function MemoryChart({
  data,
  limitBytes,
  height = 120,
  showLegend = true,
  className = '',
}: MemoryChartProps) {
  // Transform data for Recharts
  const chartData: ChartDataPoint[] = data.map(point => ({
    time: new Date(point.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
    value: point.value,
  }));

  // Calculate Y-axis domain with some padding
  const maxValue = Math.max(...data.map(d => d.value), limitBytes || 0);
  const yAxisMax = maxValue * 1.1; // 10% padding

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsAreaChart
          data={chartData}
          margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent-purple)" stopOpacity="0.4" />
              <stop offset="100%" stopColor="var(--accent-purple)" stopOpacity="0.05" />
            </linearGradient>
          </defs>

          <CartesianGrid
            stroke="var(--border-subtle)"
            strokeDasharray="3 3"
            vertical={false}
          />

          <XAxis
            dataKey="time"
            stroke="var(--text-3)"
            tick={{ fill: 'var(--text-3)', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            interval="preserveEnd"
          />

          <YAxis
            domain={[0, yAxisMax]}
            stroke="var(--text-3)"
            tick={{ fill: 'var(--text-3)', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatBytes(value)}
          />

          <Tooltip content={<MemoryCustomTooltip limitBytes={limitBytes} />} />

          {/* Limit line if provided */}
          {limitBytes && (
            <ReferenceLine
              y={limitBytes}
              stroke="var(--warning)"
              strokeDasharray="3 3"
              strokeOpacity={0.7}
              label={{
                value: 'Limit',
                fill: 'var(--warning)',
                fontSize: 10,
                position: 'top',
              }}
            />
          )}

          <Area
            type="monotone"
            dataKey="value"
            stroke="var(--accent-purple)"
            strokeWidth={2}
            fill="url(#memoryGradient)"
            dot={false}
            activeDot={{
              r: 4,
              fill: 'var(--accent-purple)',
              stroke: 'var(--bg-primary)',
              strokeWidth: 2,
            }}
            animationDuration={300}
          />
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
}

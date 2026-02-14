/**
 * CPU Chart Component
 * Line chart for CPU usage over time
 */

'use client';

import {
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import type { MetricDataPoint } from '../../types';

export interface CPUChartProps {
  /** Metric data points */
  data: MetricDataPoint[];
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
 * Custom dark theme tooltip for CPU chart
 */
function CPUCustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ value: number }> }) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  const value = payload[0].value;
  const status = value >= 90 ? 'critical' : value >= 70 ? 'warning' : 'ok';
  const statusColor =
    status === 'critical'
      ? 'var(--error)'
      : status === 'warning'
      ? 'var(--warning)'
      : 'var(--success)';

  return (
    <div className="glass-surface rounded-lg px-3 py-2 border border-border">
      <div className="text-xs text-text-3 mb-1">CPU Usage</div>
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold text-text">{value.toFixed(1)}%</span>
        <span
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: statusColor }}
        />
      </div>
    </div>
  );
}

/**
 * Line chart for CPU usage percentage
 * - Y-axis: 0-100%
 * - X-axis: time
 * - Cyan gradient stroke
 */
export function CPUChart({
  data,
  height = 120,
  showLegend = true,
  className = '',
}: CPUChartProps) {
  // Transform data for Recharts
  const chartData: ChartDataPoint[] = data.map(point => ({
    time: new Date(point.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
    value: point.value,
  }));

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart
          data={chartData}
          margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.3" />
              <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0" />
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
            domain={[0, 100]}
            stroke="var(--text-3)"
            tick={{ fill: 'var(--text-3)', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${value}%`}
          />

          <Tooltip content={<CPUCustomTooltip />} />

          {/* Warning threshold at 70% */}
          <ReferenceLine
            y={70}
            stroke="var(--warning)"
            strokeDasharray="3 3"
            strokeOpacity={0.5}
          />

          {/* Critical threshold at 90% */}
          <ReferenceLine
            y={90}
            stroke="var(--error)"
            strokeDasharray="3 3"
            strokeOpacity={0.5}
          />

          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--accent-cyan)"
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 4,
              fill: 'var(--accent-cyan)',
              stroke: 'var(--bg-primary)',
              strokeWidth: 2,
            }}
            animationDuration={300}
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}

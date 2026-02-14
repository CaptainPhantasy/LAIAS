/**
 * Network Chart Component
 * Dual-line chart for RX/TX network traffic
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
  Legend,
} from 'recharts';
import { formatBytes } from '../../lib/formatters';
import type { MetricDataPoint } from '../../types';

export interface NetworkChartProps {
  /** RX (received) data points */
  rxData: MetricDataPoint[];
  /** TX (transmitted) data points */
  txData: MetricDataPoint[];
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
  rx: number;
  tx: number;
}

/**
 * Custom dark theme tooltip for network chart
 */
function NetworkCustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
}) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <div className="glass-surface rounded-lg px-3 py-2 border border-border">
      <div className="text-xs text-text-3 mb-2">Network Traffic</div>
      <div className="space-y-1">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-text-2">{entry.name}:</span>
            <span className="text-sm font-semibold text-text">
              {formatBytes(entry.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Custom legend with colored indicators
 */
function CustomLegend() {
  return (
    <div className="flex items-center justify-center gap-6 text-xs">
      <div className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-[var(--accent-cyan)]" />
        <span className="text-text-2">RX (In)</span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-[var(--accent-pink)]" />
        <span className="text-text-2">TX (Out)</span>
      </div>
    </div>
  );
}

/**
 * Dual-line chart for network traffic
 * - RX line: cyan
 * - TX line: pink
 * - Y-axis: formatted bytes
 * - X-axis: time
 */
export function NetworkChart({
  rxData,
  txData,
  height = 120,
  showLegend = true,
  className = '',
}: NetworkChartProps) {
  // Merge RX and TX data by timestamp
  const mergedData = new Map<string, ChartDataPoint>();

  // Add RX data
  rxData.forEach(point => {
    const time = new Date(point.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    mergedData.set(time, { time, rx: point.value, tx: 0 });
  });

  // Add TX data
  txData.forEach(point => {
    const time = new Date(point.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    const existing = mergedData.get(time);
    if (existing) {
      existing.tx = point.value;
    } else {
      mergedData.set(time, { time, rx: 0, tx: point.value });
    }
  });

  // Convert to array and sort by time
  const chartData = Array.from(mergedData.values());

  // Calculate Y-axis domain with some padding
  const maxValue = Math.max(
    ...rxData.map(d => d.value),
    ...txData.map(d => d.value),
    1
  );
  const yAxisMax = maxValue * 1.1; // 10% padding

  return (
    <div className={className}>
      {showLegend && <CustomLegend />}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart
          data={chartData}
          margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
        >
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

          <Tooltip content={<NetworkCustomTooltip />} />

          {/* RX Line - Cyan */}
          <Line
            type="monotone"
            dataKey="rx"
            name="RX"
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

          {/* TX Line - Pink */}
          <Line
            type="monotone"
            dataKey="tx"
            name="TX"
            stroke="var(--accent-pink)"
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 4,
              fill: 'var(--accent-pink)',
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

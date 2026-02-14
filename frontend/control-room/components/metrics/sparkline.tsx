/**
 * Sparkline Component
 * Mini inline chart for KPI cards
 */

import { useRef, useEffect } from 'react';

export interface SparklineProps {
  /** Data points to render */
  data: number[];
  /** SVG width */
  width?: number;
  /** SVG height */
  height?: number;
  /** Stroke color (CSS variable or hex) */
  color?: string;
  /** Whether to show area fill */
  showArea?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Mini sparkline chart for KPI cards
 * Uses SVG path with optional gradient fill
 */
export function Sparkline({
  data,
  width = 80,
  height = 24,
  color = 'var(--accent-cyan)',
  showArea = true,
  className = '',
}: SparklineProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  // Generate path data from data points
  const generatePath = (values: number[], w: number, h: number): string => {
    if (values.length === 0) return '';

    const max = Math.max(...values, 1);
    const min = Math.min(...values, 0);
    const range = max - min || 1;

    const stepX = w / Math.max(values.length - 1, 1);

    // Build path commands
    let path = `M 0 ${h - ((values[0] - min) / range) * h}`;

    for (let i = 1; i < values.length; i++) {
      const x = i * stepX;
      const y = h - ((values[i] - min) / range) * h;
      path += ` L ${x} ${y}`;
    }

    return path;
  };

  const linePath = generatePath(data, width, height);

  // Generate area path (closes the loop at bottom)
  const areaPath = linePath
    ? `${linePath} L ${width} ${height} L 0 ${height} Z`
    : '';

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      className={className}
      viewBox={`0 0 ${width} ${height}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id={`sparkline-gradient-${Math.random()}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Area fill */}
      {showArea && areaPath && (
        <path
          d={areaPath}
          fill={`url(#sparkline-gradient-${Math.random()})`}
          className="transition-opacity duration-300"
        />
      )}

      {/* Line */}
      {linePath && (
        <path
          d={linePath}
          stroke={color}
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all duration-300"
        />
      )}
    </svg>
  );
}

import { LucideIcon, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface HealthIndicatorProps {
  status: 'healthy' | 'degraded' | 'unhealthy';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  label?: string;
  className?: string;
}

const HEALTH_CONFIG: Record<
  HealthIndicatorProps['status'],
  {
    defaultLabel: string;
    colorClass: string;
    bgClass: string;
    glowClass: string;
  }
> = {
  healthy: {
    defaultLabel: 'Healthy',
    colorClass: 'text-[var(--success)]',
    bgClass: 'bg-[var(--success)]',
    glowClass: 'glow-success',
  },
  degraded: {
    defaultLabel: 'Degraded',
    colorClass: 'text-[var(--warning)]',
    bgClass: 'bg-[var(--warning)]',
    glowClass: 'glow-warning',
  },
  unhealthy: {
    defaultLabel: 'Unhealthy',
    colorClass: 'text-[var(--error)]',
    bgClass: 'bg-[var(--error)]',
    glowClass: 'glow-error',
  },
};

const SIZE_CONFIG: Record<NonNullable<HealthIndicatorProps['size']>, { dot: string; text: string; icon: string }> = {
  sm: {
    dot: 'h-1.5 w-1.5',
    text: 'text-xs',
    icon: 'h-3 w-3',
  },
  md: {
    dot: 'h-2 w-2',
    text: 'text-sm',
    icon: 'h-4 w-4',
  },
  lg: {
    dot: 'h-2.5 w-2.5',
    text: 'text-base',
    icon: 'h-5 w-5',
  },
};

/**
 * HealthIndicator - Display health status as a colored dot with optional label and glow
 *
 * @param status - Health status (healthy, degraded, unhealthy)
 * @param size - Size variant (sm, md, lg) - default: md
 * @param showLabel - Whether to show the label - default: false
 * @param label - Optional custom label text
 * @param className - Additional CSS classes
 */
export function HealthIndicator({
  status,
  size = 'md',
  showLabel = false,
  label,
  className,
}: HealthIndicatorProps) {
  const config = HEALTH_CONFIG[status];
  const sizeConfig = SIZE_CONFIG[size];
  const labelText = label || config.defaultLabel;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2',
        config.colorClass,
        className
      )}
      role="status"
      aria-label={`Health: ${labelText}`}
    >
      {/* Colored dot with glow for healthy status */}
      <span
        className={cn(
          'rounded-full',
          config.bgClass,
          sizeConfig.dot,
          status === 'healthy' && config.glowClass,
          'shadow-sm'
        )}
        aria-hidden="true"
      />
      {showLabel && (
        <span className={cn('font-medium', sizeConfig.text)}>{labelText}</span>
      )}
    </div>
  );
}

/**
 * HealthBadge - Display health status as a badge with icon and optional label
 *
 * A variant of HealthIndicator that includes an icon for more visual prominence.
 */
export interface HealthBadgeProps extends HealthIndicatorProps {
  showIcon?: boolean;
}

export function HealthBadge({
  status,
  size = 'md',
  showLabel = true,
  label,
  showIcon = true,
  className,
}: HealthBadgeProps) {
  const config = HEALTH_CONFIG[status];
  const sizeConfig = SIZE_CONFIG[size];
  const labelText = label || config.defaultLabel;

  const icons: Record<HealthIndicatorProps['status'], LucideIcon> = {
    healthy: CheckCircle2,
    degraded: AlertTriangle,
    unhealthy: XCircle,
  };

  const Icon = icons[status];

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border border-[var(--border)]',
        'bg-[var(--surface)]',
        size === 'sm' && 'px-1.5 py-0.5',
        size === 'md' && 'px-2 py-1',
        size === 'lg' && 'px-3 py-1.5',
        config.colorClass,
        className
      )}
      role="status"
      aria-label={`Health: ${labelText}`}
    >
      {showIcon && (
        <Icon
          className={sizeConfig.icon}
          aria-hidden="true"
        />
      )}
      {showLabel && (
        <span className={cn('font-medium', sizeConfig.text)}>{labelText}</span>
      )}
    </div>
  );
}

import { LucideIcon, Circle, CircleDot, AlertCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface StatusBadgeProps {
  status: 'running' | 'stopped' | 'paused' | 'error' | 'pending';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  pulse?: boolean;
  children?: string;
  className?: string;
}

const STATUS_CONFIG: Record<
  StatusBadgeProps['status'],
  {
    label: string;
    icon: LucideIcon;
    colorClass: string;
    bgClass: string;
    pulse: boolean;
  }
> = {
  running: {
    label: 'Running',
    icon: CircleDot,
    colorClass: 'text-[var(--success)]',
    bgClass: 'bg-[var(--success)]',
    pulse: true,
  },
  stopped: {
    label: 'Stopped',
    icon: Circle,
    colorClass: 'text-[var(--text-3)]',
    bgClass: 'bg-[var(--text-3)]',
    pulse: false,
  },
  paused: {
    label: 'Paused',
    icon: Circle,
    colorClass: 'text-[var(--warning)]',
    bgClass: 'bg-[var(--warning)]',
    pulse: false,
  },
  error: {
    label: 'Error',
    icon: AlertCircle,
    colorClass: 'text-[var(--error)]',
    bgClass: 'bg-[var(--error)]',
    pulse: false,
  },
  pending: {
    label: 'Pending',
    icon: Clock,
    colorClass: 'text-[var(--warning)]',
    bgClass: 'bg-[var(--warning)]',
    pulse: true,
  },
};

const SIZE_CONFIG: Record<NonNullable<StatusBadgeProps['size']>, { icon: string; text: string; padding: string }> = {
  sm: {
    icon: 'h-3 w-3',
    text: 'text-xs',
    padding: 'px-1.5 py-0.5',
  },
  md: {
    icon: 'h-4 w-4',
    text: 'text-sm',
    padding: 'px-2 py-1',
  },
  lg: {
    icon: 'h-5 w-5',
    text: 'text-base',
    padding: 'px-3 py-1.5',
  },
};

/**
 * StatusBadge - Display container or service status with optional icon and pulse animation
 *
 * @param status - The status to display (running, stopped, paused, error, pending)
 * @param size - Size variant (sm, md, lg) - default: md
 * @param showIcon - Whether to show status icon - default: true
 * @param pulse - Override default pulse behavior - default: uses status default
 * @param children - Optional custom label text
 * @param className - Additional CSS classes
 */
export function StatusBadge({
  status,
  size = 'md',
  showIcon = true,
  pulse,
  children,
  className,
}: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const sizeConfig = SIZE_CONFIG[size];
  const shouldPulse = pulse ?? config.pulse;
  const labelText = children || config.label;

  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border border-[var(--border)]',
        'bg-[var(--surface)]',
        sizeConfig.padding,
        config.colorClass,
        className
      )}
      role="status"
      aria-label={`Status: ${labelText}`}
    >
      {showIcon && (
        <Icon
          className={cn(
            sizeConfig.icon,
            shouldPulse && 'status-pulse'
          )}
          aria-hidden="true"
        />
      )}
      <span className={cn('font-medium', sizeConfig.text)}>{labelText}</span>
    </span>
  );
}

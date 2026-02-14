'use client';

import * as React from 'react';
import { Circle, CircleDot, AlertCircle, Clock, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export type StatusType = 'running' | 'stopped' | 'error' | 'pending' | 'success';

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: StatusType;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  pulse?: boolean;
  children?: string;
}

// ============================================================================
// Status Config
// ============================================================================

interface StatusConfig {
  color: string;
  bgColor: string;
  borderColor: string;
  icon: React.ReactNode;
  pulse: boolean;
  label: string;
}

const statusConfigs: Record<StatusType, StatusConfig> = {
  running: {
    color: 'text-success',
    bgColor: 'bg-success/10',
    borderColor: 'border-success/30',
    icon: <CircleDot className="w-full h-full" />,
    pulse: true,
    label: 'Running',
  },
  stopped: {
    color: 'text-text-muted',
    bgColor: 'bg-surface-2',
    borderColor: 'border-border',
    icon: <Circle className="w-full h-full" />,
    pulse: false,
    label: 'Stopped',
  },
  error: {
    color: 'text-error',
    bgColor: 'bg-error/10',
    borderColor: 'border-error/30',
    icon: <AlertCircle className="w-full h-full" />,
    pulse: false,
    label: 'Error',
  },
  pending: {
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    borderColor: 'border-warning/30',
    icon: <Clock className="w-full h-full" />,
    pulse: true,
    label: 'Pending',
  },
  success: {
    color: 'text-success',
    bgColor: 'bg-success/10',
    borderColor: 'border-success/30',
    icon: <CheckCircle className="w-full h-full" />,
    pulse: false,
    label: 'Success',
  },
};

// ============================================================================
// Component
// ============================================================================

const StatusBadge = React.forwardRef<HTMLSpanElement, StatusBadgeProps>(
  (
    {
      className,
      status,
      size = 'md',
      showIcon = true,
      pulse: pulseOverride,
      children,
      ...props
    },
    ref
  ) => {
    const config = statusConfigs[status];
    const shouldPulse = pulseOverride ?? config.pulse;
    const label = children ?? config.label;

    // Size configurations
    const sizeStyles = {
      sm: {
        badge: 'text-xs px-2 py-0.5 gap-1',
        icon: 'w-3 h-3',
      },
      md: {
        badge: 'text-sm px-2.5 py-1 gap-1.5',
        icon: 'w-4 h-4',
      },
      lg: {
        badge: 'text-base px-3 py-1.5 gap-2',
        icon: 'w-5 h-5',
      },
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center font-medium rounded-full border',
          'transition-colors duration-150',
          config.color,
          config.bgColor,
          config.borderColor,
          sizeStyles[size].badge,
          className
        )}
        role="status"
        aria-label={label}
        {...props}
      >
        {showIcon && (
          <span
            className={cn(
              'relative flex-shrink-0',
              sizeStyles[size].icon,
              shouldPulse && 'animate-pulse'
            )}
          >
            {config.icon}
          </span>
        )}
        <span>{label}</span>
      </span>
    );
  }
);

StatusBadge.displayName = 'StatusBadge';

export { StatusBadge };

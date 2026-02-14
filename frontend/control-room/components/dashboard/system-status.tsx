'use client';

import * as React from 'react';
import { Database, Container, Cpu } from 'lucide-react';
import { cn } from '@/lib/utils';
import { HealthIndicator } from '@/components/status';

// ============================================================================
// Types
// ============================================================================

export interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency?: number;
  message?: string;
}

export interface SystemStatusProps {
  services: ServiceStatus[];
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

const serviceIcons: Record<string, React.ReactNode> = {
  database: <Database className="w-4 h-4" />,
  redis: <Cpu className="w-4 h-4" />,
  docker: <Container className="w-4 h-4" />,
};

export function SystemStatus({ services, className }: SystemStatusProps) {
  return (
    <div
      className={cn(
        'bg-surface border border-border rounded-lg p-6 shadow-sm',
        className
      )}
    >
      <h3 className="text-base font-semibold text-text-primary mb-4">System Status</h3>

      <div className="space-y-3">
        {services.map((service) => (
          <div
            key={service.name}
            className="flex items-center justify-between py-3 border-b border-border-subtle last:border-0"
          >
            <div className="flex items-center gap-3">
              <span className="text-text-muted">
                {serviceIcons[service.name.toLowerCase()] || <Database className="w-4 h-4" />}
              </span>
              <span className="text-sm font-medium text-text-primary capitalize">{service.name}</span>
            </div>

            <div className="flex items-center gap-3">
              {service.latency !== undefined && (
                <span className="text-xs text-text-muted">{service.latency}ms</span>
              )}
              <HealthIndicator status={service.status} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

SystemStatus.displayName = 'SystemStatus';

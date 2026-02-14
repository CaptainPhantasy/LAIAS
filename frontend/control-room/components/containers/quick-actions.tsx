'use client';

import * as React from 'react';
import { Play, Square, RefreshCw, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import type { ContainerStatus, QuickAction } from '@/types';
import { QUICK_ACTIONS } from '@/types';

// ============================================================================
// Types
// ============================================================================

export interface QuickActionsProps {
  status: ContainerStatus;
  onAction?: (action: 'start' | 'stop' | 'restart' | 'remove') => void;
  isLoading?: boolean;
  className?: string;
}

// ============================================================================
// Icons mapping
// ============================================================================

const ACTION_ICONS: Record<string, React.ReactNode> = {
  play: <Play className="w-4 h-4" />,
  square: <Square className="w-4 h-4" />,
  refresh: <RefreshCw className="w-4 h-4" />,
  trash: <Trash2 className="w-4 h-4" />,
};

// ============================================================================
// Component
// ============================================================================

export function QuickActions({
  status,
  onAction,
  isLoading = false,
  className,
}: QuickActionsProps) {
  const getActionButton = (action: QuickAction) => {
    const isDisabled = action.disabledWhen?.includes(status) || isLoading;

    return (
      <Button
        key={action.id}
        variant={action.variant === 'danger' ? 'destructive' : action.variant === 'primary' ? 'primary' : 'outline'}
        size="sm"
        onClick={() => onAction?.(action.id as 'start' | 'stop' | 'restart' | 'remove')}
        disabled={isDisabled}
        title={action.label}
      >
        {isLoading ? (
          <RefreshCw className={cn('w-4 h-4 animate-spin')} />
        ) : (
          ACTION_ICONS[action.icon]
        )}
        <span className="ml-1.5 hidden sm:inline">{action.label}</span>
      </Button>
    );
  };

  // Filter to only show lifecycle actions (not logs)
  const actions = QUICK_ACTIONS.filter(
    (action) => action.id !== 'logs'
  );

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {actions.map(getActionButton)}
    </div>
  );
}

QuickActions.displayName = 'QuickActions';

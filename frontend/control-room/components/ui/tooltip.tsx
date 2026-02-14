'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export interface TooltipProps {
  content: React.ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  children: React.ReactElement;
  className?: string;
}

// ============================================================================
// Tooltip Component
// ============================================================================

const Tooltip = ({
  content,
  placement = 'top',
  delay = 200,
  children,
  className,
}: TooltipProps) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const [position, setPosition] = React.useState({ top: 0, left: 0 });
  const triggerRef = React.useRef<HTMLElement>(null);
  const timeoutRef = React.useRef<ReturnType<typeof setTimeout>>();

  const updatePosition = React.useCallback(() => {
    if (!triggerRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = { width: 150, height: 40 }; // Approximate, will be adjusted by CSS
    const gap = 8;

    let top = 0;
    let left = 0;

    switch (placement) {
      case 'top':
        top = triggerRect.top - tooltipRect.height - gap;
        left = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        break;
      case 'bottom':
        top = triggerRect.bottom + gap;
        left = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        break;
      case 'left':
        top = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        left = triggerRect.left - tooltipRect.width - gap;
        break;
      case 'right':
        top = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        left = triggerRect.right + gap;
        break;
    }

    // Boundary checks
    const padding = 8;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (left < padding) left = padding;
    if (left + tooltipRect.width > viewportWidth - padding) {
      left = viewportWidth - tooltipRect.width - padding;
    }
    if (top < padding) top = padding;
    if (top + tooltipRect.height > viewportHeight - padding) {
      top = viewportHeight - tooltipRect.height - padding;
    }

    setPosition({ top, left });
  }, [placement]);

  const showTooltip = React.useCallback(() => {
    timeoutRef.current = setTimeout(() => {
      updatePosition();
      setIsVisible(true);
    }, delay);
  }, [delay, updatePosition]);

  const hideTooltip = React.useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  }, []);

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleMouseEnter = () => showTooltip();
  const handleMouseLeave = () => hideTooltip();
  const handleFocus = () => showTooltip();
  const handleBlur = () => hideTooltip();

  // Clone the child element and add event handlers
  const trigger = React.cloneElement(children, {
    ref: triggerRef,
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave,
    onFocus: handleFocus,
    onBlur: handleBlur,
    'aria-describedby': isVisible ? 'tooltip-content' : undefined,
  });

  const placementStyles = {
    top: 'pb-2',
    bottom: 'pt-2',
    left: 'pr-2',
    right: 'pl-2',
  };

  const arrowStyles = {
    top: 'bottom-0 left-1/2 -translate-x-1/2 translate-y-1 rotate-45',
    bottom: 'top-0 left-1/2 -translate-x-1/2 -translate-y-1 rotate-45',
    left: 'right-0 top-1/2 -translate-y-1/2 translate-x-1 rotate-45',
    right: 'left-0 top-1/2 -translate-y-1/2 -translate-x-1 rotate-45',
  };

  return (
    <>
      {trigger}
      {isVisible && (
        <div
          role="tooltip"
          id="tooltip-content"
          className={cn(
            'fixed z-50 pointer-events-none',
            'px-2.5 py-1.5 rounded-md',
            'bg-surface border border-border text-text-primary text-sm',
            'shadow-lg',
            'animate-in fade-in duration-200',
            placementStyles[placement],
            className
          )}
          style={{ top: position.top, left: position.left }}
        >
          {content}
          <span
            className={cn(
              'absolute w-2 h-2 bg-surface border border-border',
              'border-b-0 border-l-0',
              arrowStyles[placement]
            )}
          />
        </div>
      )}
    </>
  );
};

Tooltip.displayName = 'Tooltip';

export { Tooltip };

'use client';

import * as React from 'react';
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export type ToastType = 'success' | 'warning' | 'error' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

export interface ToastProps extends Toast {
  onDismiss: (id: string) => void;
}

// ============================================================================
// Toast Item Component
// ============================================================================

const ToastItem: React.FC<ToastProps> = ({
  id,
  type,
  title,
  description,
  onDismiss,
}) => {
  const icons = {
    success: <CheckCircle className="w-5 h-5 text-success" />,
    warning: <AlertTriangle className="w-5 h-5 text-warning" />,
    error: <AlertCircle className="w-5 h-5 text-error" />,
    info: <Info className="w-5 h-5 text-info" />,
  };

  const borderColors = {
    success: 'border-success/30',
    warning: 'border-warning/30',
    error: 'border-error/30',
    info: 'border-info/30',
  };

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg',
        'bg-surface border',
        'shadow-lg',
        'animate-slide-up',
        borderColors[type]
      )}
      role="alert"
    >
      <div className="flex-shrink-0">{icons[type]}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary">{title}</p>
        {description && (
          <p className="text-xs text-text-secondary mt-1">{description}</p>
        )}
      </div>
      <button
        onClick={() => onDismiss(id)}
        className={cn(
          'flex-shrink-0 p-1 rounded',
          'text-text-muted hover:text-text-primary hover:bg-surface-2',
          'transition-colors duration-150'
        )}
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

// ============================================================================
// Toast Context
// ============================================================================

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  dismissToast: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

// ============================================================================
// Toast Provider
// ============================================================================

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const addToast = React.useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const newToast: Toast = { ...toast, id };

    setToasts((prev) => [...prev, newToast]);

    // Auto dismiss
    const duration = toast.duration ?? 5000;
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);
  }, []);

  const dismissToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, dismissToast }}>
      {children}
      {/* Toast Container */}
      <div className="fixed bottom-4 right-4 z-[var(--z-toast)] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <ToastItem {...toast} onDismiss={dismissToast} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

// ============================================================================
// Hook for easy toast usage
// ============================================================================

export function useToaster() {
  const { addToast } = useToast();

  return React.useMemo(
    () => ({
      success: (title: string, description?: string) =>
        addToast({ type: 'success', title, description }),
      warning: (title: string, description?: string) =>
        addToast({ type: 'warning', title, description }),
      error: (title: string, description?: string) =>
        addToast({ type: 'error', title, description }),
      info: (title: string, description?: string) =>
        addToast({ type: 'info', title, description }),
    }),
    [addToast]
  );
}

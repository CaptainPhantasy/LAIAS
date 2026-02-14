'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface ToastProps {
  id?: string;
  variant?: ToastVariant;
  title?: string;
  description?: string;
  duration?: number;
  onClose?: () => void;
  className?: string;
}

export interface ToastContextValue {
  toast: (props: Omit<ToastProps, 'id'>) => string;
  dismiss: (id: string) => void;
  dismissAll: () => void;
}

const ToastContext = React.createContext<ToastContextValue | undefined>(undefined);

// ============================================================================
// Toast Provider
// ============================================================================

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  const [toasts, setToasts] = React.useState<Array<ToastProps & { id: string }>>([]);
  const toastIds = React.useRef(new Set<string>());

  const toast = React.useCallback((props: Omit<ToastProps, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast = { ...props, id };

    toastIds.current.add(id);
    setToasts((prev) => [...prev, newToast]);

    if (props.duration !== Infinity) {
      setTimeout(() => {
        dismiss(id);
      }, props.duration || 5000);
    }

    return id;
  }, []);

  const dismiss = React.useCallback((id: string) => {
    toastIds.current.delete(id);
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const dismissAll = React.useCallback(() => {
    toastIds.current.clear();
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ toast, dismiss, dismissAll }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
};

// ============================================================================
// Hook
// ============================================================================

export const useToast = () => {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

// ============================================================================
// Toast Component
// ============================================================================

const Toast = ({
  variant = 'info',
  title,
  description,
  onClose,
  className,
}: ToastProps) => {
  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <AlertCircle className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />,
  };

  const variantStyles = {
    success: 'border-success/30 bg-success/10 text-success',
    error: 'border-error/30 bg-error/10 text-error',
    warning: 'border-warning/30 bg-warning/10 text-warning',
    info: 'border-info/30 bg-info/10 text-info',
  };

  return (
    <div
      className={cn(
        'relative flex items-start gap-3 p-4 rounded-lg border shadow-lg',
        'animate-in slide-in-from-right-full duration-300 ease-out',
        variantStyles[variant],
        className
      )}
    >
      <div className="flex-shrink-0 mt-0.5">{icons[variant]}</div>
      <div className="flex-1 min-w-0">
        {title && (
          <p className="text-sm font-semibold text-text-primary">{title}</p>
        )}
        {description && (
          <p className="text-sm text-text-secondary mt-0.5">{description}</p>
        )}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 text-text-secondary hover:text-text-primary transition-colors"
          aria-label="Close toast"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

Toast.displayName = 'Toast';

// ============================================================================
// Toast Container
// ============================================================================

const ToastContainer = ({
  toasts,
  onDismiss,
}: {
  toasts: Array<ToastProps & { id: string }>;
  onDismiss: (id: string) => void;
}) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          {...toast}
          onClose={() => onDismiss(toast.id!)}
        />
      ))}
    </div>
  );
};

ToastContainer.displayName = 'ToastContainer';

export { Toast };

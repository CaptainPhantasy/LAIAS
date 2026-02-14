'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface ModalProps {
  isOpen?: boolean;
  onClose?: () => void;
  title?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg';
  showCloseButton?: boolean;
  children: React.ReactNode;
  className?: string;
}

export interface ModalHeaderProps {
  title?: string;
  description?: string;
  onClose?: () => void;
  showCloseButton?: boolean;
}

export interface ModalBodyProps extends React.HTMLAttributes<HTMLDivElement> {}

export interface ModalFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

// ============================================================================
// Modal Component
// ============================================================================

const Modal = ({
  isOpen = false,
  onClose,
  title,
  description,
  size = 'md',
  showCloseButton = true,
  children,
  className,
}: ModalProps) => {
  const [isMounted, setIsMounted] = React.useState(false);

  React.useEffect(() => {
    setIsMounted(true);
    return () => setIsMounted(false);
  }, []);

  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isMounted || !isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && onClose) {
      onClose();
    }
  };

  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && onClose) {
      onClose();
    }
  };

  React.useEffect(() => {
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className={cn(
          'relative z-10 w-full max-h-[90vh] overflow-hidden',
          'bg-surface border border-border rounded-lg shadow-2xl',
          'flex flex-col',

          // Size variants
          {
            'max-w-sm': size === 'sm',
            'max-w-lg': size === 'md',
            'max-w-2xl': size === 'lg',
          },

          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {(title || description || showCloseButton) && (
          <div className="flex items-start justify-between p-4 border-b border-border">
            <div className="flex-1 min-w-0">
              {title && (
                <h2 className="text-lg font-semibold text-text-primary">
                  {title}
                </h2>
              )}
              {description && (
                <p className="text-sm text-text-secondary mt-1">{description}</p>
              )}
            </div>
            {showCloseButton && onClose && (
              <button
                onClick={onClose}
                className="flex-shrink-0 ml-4 text-text-secondary hover:text-text-primary transition-colors"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-4">{children}</div>
      </div>
    </div>
  );
};

// ============================================================================
// ModalHeader Component
// ============================================================================

const ModalHeader = ({ title, description, onClose, showCloseButton = true }: ModalHeaderProps) => {
  return (
    <div className="flex items-start justify-between p-4 border-b border-border">
      <div className="flex-1 min-w-0">
        {title && (
          <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
        )}
        {description && (
          <p className="text-sm text-text-secondary mt-1">{description}</p>
        )}
      </div>
      {showCloseButton && onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 ml-4 text-text-secondary hover:text-text-primary transition-colors"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>
      )}
    </div>
  );
};

ModalHeader.displayName = 'ModalHeader';

// ============================================================================
// ModalBody Component
// ============================================================================

const ModalBody = React.forwardRef<HTMLDivElement, ModalBodyProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex-1 overflow-y-auto p-4', className)} {...props} />
  )
);

ModalBody.displayName = 'ModalBody';

// ============================================================================
// ModalFooter Component
// ============================================================================

const ModalFooter = React.forwardRef<HTMLDivElement, ModalFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('p-4 border-t border-border flex items-center justify-end gap-3', className)}
      {...props}
    />
  )
);

ModalFooter.displayName = 'ModalFooter';

export { Modal, ModalHeader, ModalBody, ModalFooter };

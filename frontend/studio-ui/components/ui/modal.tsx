'use client';

import * as React from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

// ============================================================================
// Types
// ============================================================================

export interface ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

export interface ModalContentProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface ModalHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
}

// ============================================================================
// Modal Component
// ============================================================================

const Modal: React.FC<ModalProps> = ({ open, onOpenChange, children }) => {
  // Handle escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onOpenChange(false);
      }
    };

    if (open) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={() => onOpenChange(false)}
      />

      {/* Content */}
      <div className="relative z-10 animate-slide-up">{children}</div>
    </div>
  );
};

// ============================================================================
// ModalContent Component
// ============================================================================

const ModalContent = React.forwardRef<HTMLDivElement, ModalContentProps>(
  ({ className, size = 'md', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'relative bg-surface border border-border rounded-xl shadow-xl',
          'max-h-[90vh] overflow-auto',
          'animate-slide-up',

          // Size
          {
            'w-full max-w-sm': size === 'sm',
            'w-full max-w-md': size === 'md',
            'w-full max-w-lg': size === 'lg',
            'w-full max-w-2xl': size === 'xl',
          },

          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

ModalContent.displayName = 'ModalContent';

// ============================================================================
// ModalHeader Component
// ============================================================================

const ModalHeader = React.forwardRef<HTMLDivElement, ModalHeaderProps>(
  ({ className, title, description, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex items-start justify-between gap-4 p-6 pb-0', className)}
        {...props}
      >
        <div>
          <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
          {description && (
            <p className="text-sm text-text-secondary mt-1">{description}</p>
          )}
          {children}
        </div>
      </div>
    );
  }
);

ModalHeader.displayName = 'ModalHeader';

// ============================================================================
// ModalBody Component
// ============================================================================

const ModalBody = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6', className)} {...props} />
));

ModalBody.displayName = 'ModalBody';

// ============================================================================
// ModalFooter Component
// ============================================================================

const ModalFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    onClose?: () => void;
    closeText?: string;
  }
>(({ className, children, onClose, closeText = 'Cancel', ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex items-center justify-end gap-3 p-6 pt-0 mt-4',
      className
    )}
    {...props}
  >
    {onClose && (
      <Button variant="ghost" onClick={onClose}>
        {closeText}
      </Button>
    )}
    {children}
  </div>
));

ModalFooter.displayName = 'ModalFooter';

// ============================================================================
// ModalClose Component
// ============================================================================

const ModalClose: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button
    onClick={onClick}
    className={cn(
      'absolute top-4 right-4',
      'p-2 rounded-md',
      'text-text-muted hover:text-text-primary hover:bg-surface-2',
      'transition-colors duration-150',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan'
    )}
  >
    <X className="w-5 h-5" />
  </button>
);

export { Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, ModalClose };

'use client';

import { useEffect } from 'react';

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Page error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-primary">
      <div className="text-center space-y-4 p-8">
        <div className="w-12 h-12 mx-auto rounded-full bg-red-500/20 flex items-center justify-center">
          <span className="text-red-400 text-xl">!</span>
        </div>
        <h2 className="text-xl font-semibold text-text-primary">Something went wrong</h2>
        <p className="text-text-secondary max-w-md">
          {error.message || 'An unexpected error occurred'}
        </p>
        <button
          type="button"
          onClick={reset}
          className="px-4 py-2 bg-accent-cyan/20 text-accent-cyan rounded-lg hover:bg-accent-cyan/30 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

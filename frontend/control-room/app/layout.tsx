import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { StackProvider, StackTheme } from '@stackframe/stack';
import { stackClientApp } from '@/stack/client';
import '@/styles/globals.css';
import '@/styles/variables.css';
import { AppShell } from '@/components/layout';

// ============================================================================
// Fonts
// ============================================================================

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
  fallback: ['system-ui', 'sans-serif'],
});

// ============================================================================
// Metadata
// ============================================================================

export const metadata: Metadata = {
  title: 'Control Room | LAIAS',
  description: 'Monitor and manage deployed AI agent containers',
  icons: {
    icon: '/favicon.ico',
  },
};

// ============================================================================
// Root Layout
// ============================================================================

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased">
        <StackProvider app={stackClientApp}>
          <StackTheme>
            <AppShell>{children}</AppShell>
          </StackTheme>
        </StackProvider>
      </body>
    </html>
  );
}

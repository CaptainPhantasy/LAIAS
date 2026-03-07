import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { StackProvider, StackTheme } from '@stackframe/stack';
import { stackClientApp } from '@/stack/client';
import '@/styles/globals.css';
import '@/styles/variables.css';
import { ToastProvider } from '@/components/ui/toast';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
  fallback: ['system-ui', 'sans-serif'],
});

export const metadata: Metadata = {
  title: 'LAIAS Studio',
  description: 'Build and deploy AI agents with natural language',
  icons: {
    icon: '/favicon.ico',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#0B1020',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="dark" className={inter.variable}>
      <body className="font-sans min-h-screen bg-bg-primary text-text-primary antialiased">
        <StackProvider app={stackClientApp}>
          <StackTheme>
            <ToastProvider>
              {children}
            </ToastProvider>
          </StackTheme>
        </StackProvider>
      </body>
    </html>
  );
}

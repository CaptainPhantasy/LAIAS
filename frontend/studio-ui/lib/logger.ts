/**
 * Client-side logging utility for LAIAS Studio UI.
 *
 * Provides structured logging with levels, context, and error tracking.
 * In development, logs to console. In production, can be configured to
 * send to a logging service (Sentry, LogRocket, etc.)
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
}

interface LoggerConfig {
  /** Minimum log level to output */
  minLevel: LogLevel;
  /** Enable console output */
  consoleOutput: boolean;
  /** Remote logging endpoint (optional) */
  remoteEndpoint?: string;
  /** Application context to include in all logs */
  appContext?: Record<string, unknown>;
}

// Default configuration
const defaultConfig: LoggerConfig = {
  minLevel: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  consoleOutput: true,
  appContext: {
    app: 'studio-ui',
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  },
};

// Level priority for filtering
const levelPriority: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

class Logger {
  private config: LoggerConfig;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...defaultConfig, ...config };
  }

  /**
   * Update logger configuration.
   */
  configure(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Log a debug message.
   */
  debug(message: string, context?: Record<string, unknown>): void {
    this.log('debug', message, context);
  }

  /**
   * Log an info message.
   */
  info(message: string, context?: Record<string, unknown>): void {
    this.log('info', message, context);
  }

  /**
   * Log a warning message.
   */
  warn(message: string, context?: Record<string, unknown>): void {
    this.log('warn', message, context);
  }

  /**
   * Log an error message with optional error object.
   */
  error(message: string, error?: Error | unknown, context?: Record<string, unknown>): void {
    const entry: LogEntry = this.createEntry('error', message, context);

    if (error instanceof Error) {
      entry.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    } else if (error) {
      entry.context = { ...entry.context, rawError: error };
    }

    this.output(entry);
  }

  /**
   * Log a user action for analytics.
   */
  action(action: string, context?: Record<string, unknown>): void {
    this.log('info', `User action: ${action}`, { action, ...context });
  }

  /**
   * Log an API call.
   */
  apiCall(method: string, endpoint: string, context?: Record<string, unknown>): void {
    this.log('debug', `API ${method} ${endpoint}`, { method, endpoint, ...context });
  }

  /**
   * Log an API response.
   */
  apiResponse(method: string, endpoint: string, status: number, duration: number): void {
    const level = status >= 400 ? 'warn' : 'debug';
    this.log(level, `API ${method} ${endpoint} → ${status}`, { method, endpoint, status, duration });
  }

  /**
   * Log an API error.
   */
  apiError(method: string, endpoint: string, error: Error | unknown): void {
    this.error(`API ${method} ${endpoint} failed`, error, { method, endpoint });
  }

  // Private methods

  private log(level: LogLevel, message: string, context?: Record<string, unknown>): void {
    if (levelPriority[level] < levelPriority[this.config.minLevel]) {
      return;
    }

    const entry = this.createEntry(level, message, context);
    this.output(entry);
  }

  private createEntry(level: LogLevel, message: string, context?: Record<string, unknown>): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: { ...this.config.appContext, ...context },
    };
  }

  private output(entry: LogEntry): void {
    // Console output
    if (this.config.consoleOutput) {
      const consoleMethod = entry.level === 'debug' ? 'log' : entry.level;
      const prefix = `[${entry.timestamp}] [${entry.level.toUpperCase()}]`;

      if (entry.error) {
        console[consoleMethod](prefix, entry.message, entry.context || '', entry.error);
      } else {
        console[consoleMethod](prefix, entry.message, entry.context || '');
      }
    }

    // Remote logging (if configured)
    if (this.config.remoteEndpoint && entry.level !== 'debug') {
      this.sendToRemote(entry).catch(() => {
        // Silently fail - don't want logging errors to cause more errors
      });
    }
  }

  private async sendToRemote(entry: LogEntry): Promise<void> {
    if (!this.config.remoteEndpoint) return;

    try {
      // Use sendBeacon for reliability, fallback to fetch
      const data = JSON.stringify(entry);

      if (navigator.sendBeacon) {
        navigator.sendBeacon(this.config.remoteEndpoint, data);
      } else {
        await fetch(this.config.remoteEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: data,
          keepalive: true,
        });
      }
    } catch {
      // Silently fail
    }
  }
}

// Singleton logger instance
export const logger = new Logger();

// Export for custom configuration
export { Logger, type LoggerConfig, type LogLevel, type LogEntry };

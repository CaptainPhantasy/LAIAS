/**
 * Number formatting utilities
 */

/**
 * Format bytes to human readable string
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

/**
 * Format number with thousands separator
 */
export function formatNumber(num: number, locale: string = 'en-US'): string {
  return new Intl.NumberFormat(locale).format(num);
}

/**
 * Format percentage
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format CPU percentage with color coding indicator
 */
export function formatCPU(value: number): { text: string; status: 'ok' | 'warning' | 'critical' } {
  const text = formatPercent(value);
  let status: 'ok' | 'warning' | 'critical' = 'ok';

  if (value >= 90) {
    status = 'critical';
  } else if (value >= 70) {
    status = 'warning';
  }

  return { text, status };
}

/**
 * Format memory with status indicator
 */
export function formatMemory(bytes: number, limit?: number): { text: string; percent?: number; status: 'ok' | 'warning' | 'critical' } {
  const text = formatBytes(bytes);
  let percent: number | undefined;
  let status: 'ok' | 'warning' | 'critical' = 'ok';

  if (limit) {
    percent = (bytes / limit) * 100;
    if (percent >= 90) {
      status = 'critical';
    } else if (percent >= 70) {
      status = 'warning';
    }
  }

  return { text, percent, status };
}

/**
 * Date/time formatting utilities
 */

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = typeof date === 'string' ? new Date(date) : date;
  const diffMs = now.getTime() - then.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) {
    return 'just now';
  } else if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return formatDate(then);
  }
}

/**
 * Format uptime (duration)
 */
export function formatUptime(startedAt: string | Date | undefined): string {
  if (!startedAt) return '—';

  const now = new Date();
  const start = typeof startedAt === 'string' ? new Date(startedAt) : startedAt;
  const diffMs = now.getTime() - start.getTime();

  if (diffMs < 0) return '—';

  const seconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    const remainingHours = hours % 24;
    return `${days}d ${remainingHours}h`;
  } else if (hours > 0) {
    const remainingMins = minutes % 60;
    return `${hours}h ${remainingMins}m`;
  } else if (minutes > 0) {
    return `${minutes}m`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Format date as short string (MM/DD/YYYY)
 */
export function formatDate(date: string | Date, locale: string = 'en-US'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(locale, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(d);
}

/**
 * Format time (HH:MM:SS)
 */
export function formatTime(date: string | Date, locale: string = 'en-US'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(d);
}

/**
 * Format datetime for logs
 */
export function formatLogTimestamp(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();

  if (isToday) {
    return formatTime(d);
  } else {
    return `${formatDate(d)} ${formatTime(d)}`;
  }
}

/**
 * Format ISO timestamp
 */
export function formatTimestamp(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toISOString();
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 3)}...`;
}

/**
 * Truncate container ID (first 12 chars)
 */
export function truncateId(id: string, length: number = 12): string {
  if (!id) return '—';
  return id.slice(0, length);
}

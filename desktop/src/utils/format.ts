import { formatDistanceToNow, format } from "date-fns";

/** Format bytes to human-readable size string. */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["B", "KB", "MB", "GB", "TB", "PB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

/** Format seconds to human-readable uptime string. */
export function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  if (m > 0 || parts.length === 0) parts.push(`${m}m`);
  return parts.join(" ");
}

/** Format a Date to relative time (e.g. "3 minutes ago"). */
export function timeAgo(date: Date): string {
  return formatDistanceToNow(date, { addSuffix: true });
}

/** Format a Date to a short readable time (e.g. "10:32 AM"). */
export function formatTime(date: Date): string {
  return format(date, "h:mm a");
}

/** Format a percentage value clamped to 0–100. */
export function formatPercent(value: number, decimals = 0): string {
  const clamped = Math.max(0, Math.min(100, value));
  return `${clamped.toFixed(decimals)}%`;
}

/** Generate a random UUID v4. */
export function generateId(): string {
  return crypto.randomUUID();
}

/** Truncate a string to a max length with ellipsis. */
export function truncate(str: string, max: number): string {
  if (str.length <= max) return str;
  return str.slice(0, max - 3) + "...";
}

/** Convert a Windows path to a display-friendly string. */
export function displayPath(path: string): string {
  // Replace user home with ~ for brevity
  return path.replace(/^C:\\Users\\[^\\]+/, "~");
}

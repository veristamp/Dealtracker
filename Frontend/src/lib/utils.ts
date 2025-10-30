// src/lib/utils.ts (Simplified Fix)

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { formatDistanceToNow, parseISO } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Parses a UTC ISO string and returns its distance from now in local time.
 * e.g., "5 minutes ago"
 * @param timestamp - The UTC timestamp string from the backend.
 * @returns A formatted string representing the relative time.
 */
export function formatTimestamp(timestamp?: string): string {
  if (!timestamp) {
    return 'Never';
  }
  try {
    const date = parseISO(timestamp);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch (error) {
    console.error('Invalid timestamp format:', error);
    return 'Invalid Date';
  }
}

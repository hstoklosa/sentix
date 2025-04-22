import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines multiple class names or class value objects into a single string using clsx and tailwind-merge.
 * This utility helps prevent class name conflicts and duplicates when using Tailwind CSS.
 *
 * @param inputs - array of class values (strings, objects, arrays, etc.) to be merged
 * @returns a merged string of class names optimized for Tailwind CSS
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrencyAmount(value: number): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  } else if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  } else if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  } else {
    return value.toString();
  }
}

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines multiple class names or class value objects into a single string using clsx and tailwind-merge.
 * This utility helps prevent class name conflicts and duplicates when using Tailwind CSS.
 *
 * @param inputs - array of class values (strings, objects, arrays, etc.) to be merged
 * @returns a merged string of class names optimized for Tailwind CSS
 *
 * @example
 * cn('p-4', 'bg-blue-500', { 'text-white': true, 'rounded': false })
 *  => 'p-4 bg-blue-500 text-white'
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

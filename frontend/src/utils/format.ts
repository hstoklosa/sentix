/**
 * Formats a timestamp into a human-readable relative time string.
 *
 * @param timestamp - ISO 8601 timestamp string to format
 * @returns Formatted relative time string (e.g., "2s", "5min", "3h", "2d", "1w", "3m", "2y")
 */
export const formatRelativeTime = (timestamp: string): string => {
  const now = Date.now();
  const date = new Date(timestamp).getTime();
  const diffSeconds = Math.floor((now - date) / 1000);

  const TIME_UNITS = [
    { max: 60, label: "s" },
    { max: 3600, label: "min", divider: 60 },
    { max: 86400, label: "h", divider: 3600 },
    { max: 604800, label: "d", divider: 86400 },
    { max: 2628000, label: "w", divider: 604800 },
    { max: 31536000, label: "m", divider: 2628000 },
    { max: Infinity, label: "y", divider: 31536000 },
  ];

  const unit =
    TIME_UNITS.find((unit) => diffSeconds < unit.max) ||
    TIME_UNITS[TIME_UNITS.length - 1];
  const value = Math.floor(diffSeconds / (unit.divider || 1));

  return `${value}${unit.label}`;
};

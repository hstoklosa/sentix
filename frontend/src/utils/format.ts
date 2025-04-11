/**
 * Formats a timestamp into a human-readable relative time string.
 * Properly handles ISO 8601 formatted date strings with timezone information.
 *
 * @param timestamp - ISO 8601 timestamp string to format
 * @returns Formatted relative time string (e.g., "2s", "5min", "3h", "2d", "1w", "3m", "2y")
 */
export const formatRelativeTime = (timestamp: string): string => {
  if (!timestamp) return "-";

  try {
    // Parse ISO 8601 formatted date with timezone support
    const date = new Date(timestamp);

    // Validate the date is valid
    if (isNaN(date.getTime())) {
      console.error("Invalid date format:", timestamp);
      return "-";
    }

    const now = Date.now();
    const diffSeconds = Math.floor((now - date.getTime()) / 1000);

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
  } catch (error) {
    console.error("Error formatting relative time:", error);
    return "-";
  }
};

/**
 * Formats a date string into a localised date and time string in 12-hour format.
 * Properly handles ISO 8601 formatted date strings with timezone information.
 *
 * @param dateString - ISO 8601 date string to format
 * @returns Formatted string in the format "MM/DD/YYYY, H:MM am/pm"
 * @example
 * formatDateTime("2024-02-14T09:30:00Z") // Returns "02/14/2024, 9:30 am"
 */
export const formatDateTime = (dateString: string) => {
  try {
    const date = new Date(dateString);

    // Validate the date is valid
    if (isNaN(date.getTime())) {
      console.error("Invalid date format:", dateString);
      return "-";
    }

    return (
      date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }) +
      ", " +
      date
        .toLocaleTimeString(undefined, {
          hour: "numeric",
          minute: "2-digit",
          hour12: true,
        })
        .toLowerCase()
    );
  } catch (error) {
    console.error("Error formatting datetime:", error);
    return "-";
  }
};

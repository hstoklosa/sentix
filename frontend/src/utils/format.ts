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

/**
 * Formats a number into a compact representation with optional currency symbol and decimal places.
 * Converts numbers to compact form like 1k, 1m, 1b, 1t (or 1K, 1M, 1B, 1T if uppercase is true)
 *
 * @param value - Number to format
 * @param decimals - Number of decimal places (default: 1)
 * @param currency - Currency symbol to prepend (default: '')
 * @param uppercase - Whether to use uppercase unit symbols (default: false)
 * @returns Formatted compact number string
 * @example
 * formatCompactNumber(1234) // Returns "1.2k"
 * formatCompactNumber(1234567, 2) // Returns "1.23m"
 * formatCompactNumber(1234567, 1, "$") // Returns "$1.2m"
 * formatCompactNumber(1234567, 1, "$", true) // Returns "$1.2M"
 */
export const formatCompactNumber = (
  value: number,
  decimals: number = 1,
  currency: string = "",
  uppercase: boolean = false
): string => {
  try {
    if (!Number.isFinite(value)) return "-";

    const units = [
      { value: 1e12, symbol: "t" },
      { value: 1e9, symbol: "b" },
      { value: 1e6, symbol: "m" },
      { value: 1e3, symbol: "k" },
    ];

    const unit = units.find((unit) => Math.abs(value) >= unit.value);
    if (!unit) {
      // Format values < 1000 with the specified decimals
      const formatted = value.toFixed(decimals).replace(/\.?0+$/, "");
      return `${currency}${formatted}`;
    }

    const formatted = (value / unit.value).toFixed(decimals).replace(/\.?0+$/, "");
    const symbol = uppercase ? unit.symbol.toUpperCase() : unit.symbol;
    return `${currency}${formatted}${symbol}`;
  } catch (error) {
    console.error("Error formatting compact number:", error);
    return "-";
  }
};

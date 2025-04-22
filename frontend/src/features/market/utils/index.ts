/**
 * Formats a price to a more readable format
 * e.g. 95000 -> 95k, 1200000 -> 1.2M
 */
export const formatPrice = (price: number): string => {
  if (price >= 1000000) {
    return `${(price / 1000000).toFixed(1)}M`;
  }
  if (price >= 1000) {
    return `${(price / 1000).toFixed(1)}k`;
  }
  return price.toFixed(2);
};

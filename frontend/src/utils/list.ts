/**
 * Helper function to check if two sets have the same elements
 */
export const setsAreEqual = (a: Set<number>, b: Set<number>): boolean => {
  if (a.size !== b.size) return false;
  for (const item of a) {
    if (!b.has(item)) return false;
  }
  return true;
};

/**
 * Helper function to check if two arrays have the same elements
 * regardless of order
 */
export const arraysHaveSameElements = (a: string[], b: string[]): boolean => {
  if (a.length !== b.length) return false;
  const setA = new Set(a);
  return b.every((item) => setA.has(item));
};

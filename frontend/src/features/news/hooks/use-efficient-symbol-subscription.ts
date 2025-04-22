import { useRef, useCallback, useEffect } from "react";
import useCoinSubscription from "@/features/coins/hooks/use-coin-subscription";
import { arraysHaveSameElements } from "@/utils/list";

export interface SymbolsData {
  symbols: string[];
  version: number;
}

/**
 * An efficient hook for managing WebSocket symbol subscriptions with the
 * following optimizations:
 *
 * 1. Uses a buffer period to collect symbols during rapid scrolling
 * 2. Avoids unnecessary subscription changes during scroll momentum
 * 3. Batches subscription updates for better performance
 * 4. Intelligent throttling based on scroll velocity
 */
const useEfficientSymbolSubscription = () => {
  const { subscribeToSymbols, unsubscribeFromSymbols } = useCoinSubscription();
  const subscribedSymbolsRef = useRef<string[]>([]);
  const pendingUpdateRef = useRef<NodeJS.Timeout | null>(null);
  const updateBufferRef = useRef<SymbolsData | null>(null);
  const lastUpdateTimeRef = useRef<number>(0);
  const scrollVelocityRef = useRef<number>(0);
  const lastScrollPositionRef = useRef<number>(0);
  const lastScrollTimeRef = useRef<number>(0);

  // Calculate adaptive debounce time based on scroll velocity
  const getDebounceTime = useCallback(() => {
    // Base debounce of 200ms, with up to 800ms during rapid scrolling
    return Math.min(200 + scrollVelocityRef.current * 300, 800);
  }, []);

  // Track scroll velocity to determine optimal debounce timing
  const updateScrollVelocity = useCallback((scrollTop: number) => {
    const now = performance.now();
    const timeDelta = now - lastScrollTimeRef.current;

    if (timeDelta > 0) {
      const positionDelta = Math.abs(scrollTop - lastScrollPositionRef.current);
      // Calculate pixels per millisecond, with a decay factor
      const currentVelocity = positionDelta / timeDelta;

      // Exponential moving average for smoother velocity tracking
      scrollVelocityRef.current =
        scrollVelocityRef.current * 0.7 + currentVelocity * 0.3;
    }

    lastScrollPositionRef.current = scrollTop;
    lastScrollTimeRef.current = now;
  }, []);

  // Process update after the debounce period has ended
  const processBufferedUpdate = useCallback(() => {
    const now = performance.now();
    const buffer = updateBufferRef.current;

    // Skip if no pending updates or empty symbols array
    if (!buffer || buffer.symbols.length === 0) return;

    // Reset the buffer
    updateBufferRef.current = null;

    // Skip redundant updates (same symbols as before)
    if (arraysHaveSameElements(buffer.symbols, subscribedSymbolsRef.current)) {
      return;
    }

    // Calculate symbols to add and remove
    const symbolsToRemove = subscribedSymbolsRef.current.filter(
      (symbol) => !buffer.symbols.includes(symbol)
    );

    const symbolsToAdd = buffer.symbols.filter(
      (symbol) => !subscribedSymbolsRef.current.includes(symbol)
    );

    // Process unsubscriptions
    if (symbolsToRemove.length > 0) {
      unsubscribeFromSymbols(symbolsToRemove);
    }

    // Process subscriptions
    if (symbolsToAdd.length > 0) {
      subscribeToSymbols(symbolsToAdd);
    }

    // Update our reference of currently subscribed symbols
    subscribedSymbolsRef.current = [...buffer.symbols];
    lastUpdateTimeRef.current = now;
  }, [subscribeToSymbols, unsubscribeFromSymbols]);

  // Accept new set of visible symbols during scrolling
  const updateVisibleSymbols = useCallback(
    (symbols: string[], scrollTop?: number) => {
      // Track scroll velocity if scrollTop is provided
      if (scrollTop !== undefined) {
        updateScrollVelocity(scrollTop);
      }

      // Skip empty symbol arrays
      if (!symbols.length) return;

      // Buffer the update with a version counter
      const version = (updateBufferRef.current?.version || 0) + 1;
      updateBufferRef.current = { symbols, version };

      // Cancel any pending update
      if (pendingUpdateRef.current) {
        clearTimeout(pendingUpdateRef.current);
      }

      // Use adaptive debounce time based on scroll velocity
      const debounceTime = getDebounceTime();

      // Schedule a new update after the debounce period
      pendingUpdateRef.current = setTimeout(() => {
        processBufferedUpdate();
        pendingUpdateRef.current = null;
      }, debounceTime);
    },
    [processBufferedUpdate, getDebounceTime, updateScrollVelocity]
  );

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (pendingUpdateRef.current) {
        clearTimeout(pendingUpdateRef.current);
      }

      if (subscribedSymbolsRef.current.length > 0) {
        unsubscribeFromSymbols(subscribedSymbolsRef.current);
      }
    };
  }, [unsubscribeFromSymbols]);

  return { updateVisibleSymbols };
};

export default useEfficientSymbolSubscription;

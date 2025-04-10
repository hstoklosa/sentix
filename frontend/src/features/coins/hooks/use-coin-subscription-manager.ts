import { useState, useRef, useEffect, useCallback } from "react";

import useBinanceWebSocket from "./use-binance-websocket";

// Common cryptocurrencies that should always stay subscribed
const PINNED_SYMBOLS = ["BTC", "ETH", "BNB", "SOL", "XRP"];

/**
 * Hook for centralized management of cryptocurrency symbol subscriptions.
 * This solves the problem of individual components subscribing/unsubscribing
 * to the same symbols, especially in virtualized lists where components
 * mount/unmount frequently during scrolling.
 */
export function useCoinSubscriptionManager() {
  const { subscribeToSymbol, unsubscribeFromSymbol } = useBinanceWebSocket();
  const debouncedUpdateRef = useRef<NodeJS.Timeout | null>(null);

  // Track all desired symbol subscriptions (pinned + visible)
  const [desiredSymbols, setDesiredSymbols] = useState<Set<string>>(
    new Set(PINNED_SYMBOLS)
  );
  const pinnedSymbolsRef = useRef<Set<string>>(new Set(PINNED_SYMBOLS));

  /**
   * Update the set of visible symbols with debouncing to prevent
   * rapid subscription changes during scrolling
   */
  const updateVisibleSymbols = useCallback(
    (newVisibleSymbols: string[]) => {
      if (debouncedUpdateRef.current) {
        clearTimeout(debouncedUpdateRef.current);
      }

      debouncedUpdateRef.current = setTimeout(() => {
        // Calculate the new complete set of desired subscriptions
        const pinnedSymbols = pinnedSymbolsRef.current;
        const newDesiredSet = new Set([...pinnedSymbols, ...newVisibleSymbols]);

        // Calculate what needs to be subscribed vs unsubscribed
        const toSubscribe = [...newDesiredSet].filter(
          (s) => !desiredSymbols.has(s)
        );
        const toUnsubscribe = [...desiredSymbols].filter(
          (s) => !newDesiredSet.has(s) && !pinnedSymbols.has(s)
        );

        // Log only if there are changes
        if (toSubscribe.length || toUnsubscribe.length) {
          console.log(
            `[CoinSubscriptionManager] Updating subscriptions: +${toSubscribe.length} -${toUnsubscribe.length}`
          );

          // Only make necessary subscription changes
          toSubscribe.forEach(subscribeToSymbol);
          toUnsubscribe.forEach(unsubscribeFromSymbol);
        }

        // Update our state
        setDesiredSymbols(newDesiredSet);
      }, 300); // Debounce window
    },
    [desiredSymbols, subscribeToSymbol, unsubscribeFromSymbol]
  );

  // Subscribe to pinned symbols on mount
  useEffect(() => {
    console.log(
      `[CoinSubscriptionManager] Pre-loading pinned symbols: ${PINNED_SYMBOLS.join(", ")}`
    );

    // Subscribe to all pinned symbols
    PINNED_SYMBOLS.forEach(subscribeToSymbol);

    // Clean up on unmount
    return () => {
      console.log(`[CoinSubscriptionManager] Cleaning up all subscriptions`);

      // Unsubscribe from everything
      [...desiredSymbols].forEach(unsubscribeFromSymbol);
    };
  }, [subscribeToSymbol, unsubscribeFromSymbol]);

  // Clean up debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debouncedUpdateRef.current) {
        clearTimeout(debouncedUpdateRef.current);
      }
    };
  }, []);

  return {
    updateVisibleSymbols,
    // For debugging purposes
    subscribedSymbols: Array.from(desiredSymbols),
  };
}

export default useCoinSubscriptionManager;

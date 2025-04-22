import { useEffect, useRef, useCallback } from "react";
import useBinanceWebSocket from "./use-binance-websocket";

const subscriptionCounters = new Map<string, number>();

/**
 * Component-level coin subscription hook with reference counting
 *
 * This hook provides component-safe symbol subscription that won't interfere
 * with other components. It maintains a global reference count for each symbol,
 * so symbols are only unsubscribed when no components are using them.
 */
const useCoinSubscription = () => {
  const { subscribeToSymbol, unsubscribeFromSymbol } = useBinanceWebSocket();
  const subscribedSymbolsRef = useRef<Set<string>>(new Set());

  // Subscribe to a symbol with reference counting
  const subscribe = useCallback(
    (symbol: string) => {
      if (!symbol) return;

      const currentCount = subscriptionCounters.get(symbol) || 0;

      // Only call the actual subscribe if this is the first reference
      if (currentCount === 0) {
        subscribeToSymbol(symbol);
      }

      // Increment the counter and track in this component
      subscriptionCounters.set(symbol, currentCount + 1);
      subscribedSymbolsRef.current.add(symbol);
    },
    [subscribeToSymbol]
  );

  const unsubscribe = useCallback(
    (symbol: string) => {
      if (!symbol || !subscribedSymbolsRef.current.has(symbol)) return;

      const currentCount = subscriptionCounters.get(symbol) || 0;
      if (currentCount <= 0) {
        return;
      }

      const newCount = currentCount - 1;
      subscriptionCounters.set(symbol, newCount);
      subscribedSymbolsRef.current.delete(symbol);

      if (newCount === 0) {
        unsubscribeFromSymbol(symbol);
      }
    },
    [unsubscribeFromSymbol]
  );

  const subscribeToSymbols = useCallback(
    (symbols: string[]) => {
      if (!symbols.length) return;
      symbols.forEach(subscribe);
    },
    [subscribe]
  );

  const unsubscribeFromSymbols = useCallback(
    (symbols: string[]) => {
      if (!symbols.length) return;
      symbols.forEach(unsubscribe);
    },
    [unsubscribe]
  );

  useEffect(() => {
    return () => {
      // Unsubscribe from all symbols this component subscribed to
      const symbols = Array.from(subscribedSymbolsRef.current);
      symbols.forEach(unsubscribe);
    };
  }, [unsubscribe]);

  return {
    subscribeToSymbol: subscribe,
    unsubscribeFromSymbol: unsubscribe,
    subscribeToSymbols,
    unsubscribeFromSymbols,
  };
};

export default useCoinSubscription;

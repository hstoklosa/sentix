import { useEffect, useRef, useCallback } from "react";
import useBinanceWebSocket from "./use-binance-websocket";

const subscriptionCounters = new Map<string, number>();

/**
 * Component-level coin subscription hook with reference counting
 *
 * This hook provides component-safe symbol subscription that won't
 * interfere with other components. It maintains a global reference
 * count for each symbol, so symbols are only unsubscribed when no
 * components are using them.
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
        console.log(`[ComponentSub] First subscription to ${symbol}`);
        subscribeToSymbol(symbol);
      }

      // Increment the counter and track in this component
      subscriptionCounters.set(symbol, currentCount + 1);
      subscribedSymbolsRef.current.add(symbol);

      console.log(`[ComponentSub] ${symbol} has ${currentCount + 1} subscribers`);
    },
    [subscribeToSymbol]
  );

  // Unsubscribe from a symbol with reference counting
  const unsubscribe = useCallback(
    (symbol: string) => {
      if (!symbol || !subscribedSymbolsRef.current.has(symbol)) return;

      const currentCount = subscriptionCounters.get(symbol) || 0;

      if (currentCount <= 0) {
        console.warn(
          `[ComponentSub] Trying to unsubscribe from ${symbol} but counter is already at ${currentCount}`
        );
        return;
      }

      // Decrement the counter
      const newCount = currentCount - 1;
      subscriptionCounters.set(symbol, newCount);
      subscribedSymbolsRef.current.delete(symbol);

      // Only call the actual unsubscribe if this was the last reference
      if (newCount === 0) {
        console.log(`[ComponentSub] Last subscriber to ${symbol} unsubscribed`);
        unsubscribeFromSymbol(symbol);
      }

      console.log(`[ComponentSub] ${symbol} has ${newCount} subscribers left`);
    },
    [unsubscribeFromSymbol]
  );

  // Batch subscribe to multiple symbols
  const subscribeToSymbols = useCallback(
    (symbols: string[]) => {
      if (!symbols.length) return;
      symbols.forEach(subscribe);
    },
    [subscribe]
  );

  // Batch unsubscribe from multiple symbols
  const unsubscribeFromSymbols = useCallback(
    (symbols: string[]) => {
      if (!symbols.length) return;
      symbols.forEach(unsubscribe);
    },
    [unsubscribe]
  );

  // Clean up all subscriptions when component unmounts
  useEffect(() => {
    return () => {
      // Unsubscribe from all symbols this component subscribed to
      const symbols = Array.from(subscribedSymbolsRef.current);
      console.log(
        `[ComponentSub] Cleanup: unsubscribing from ${symbols.length} symbols`
      );
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

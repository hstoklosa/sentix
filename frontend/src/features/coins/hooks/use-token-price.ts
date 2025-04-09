import { useEffect, useMemo } from "react";

import useBinanceWebSocket from "./use-binance-websocket";
import { usePriceStore } from "./use-price-store";

export const useTokenPrice = (symbol: string) => {
  const { subscribeToSymbol, unsubscribeFromSymbol } = useBinanceWebSocket();

  // Use a memoized selector key to ensure consistent reference
  const selectorKey = useMemo(() => (symbol ? symbol.toUpperCase() : ""), [symbol]);
  const price = usePriceStore((state) => state.getPrice(selectorKey));

  useEffect(() => {
    if (!symbol) return;

    subscribeToSymbol(symbol);
    return () => unsubscribeFromSymbol(symbol);
  }, [symbol, subscribeToSymbol, unsubscribeFromSymbol]);

  return price;
};

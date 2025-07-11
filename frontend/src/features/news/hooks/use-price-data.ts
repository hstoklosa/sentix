import { useMemo } from "react";
import { usePriceStore } from "@/features/coins/hooks/use-price-store";

interface PriceData {
  price?: number;
  changePercent?: number;
}

interface CoinPriceData {
  [symbol: string]: PriceData;
}

/**
 * A hook that batches price data requests for multiple coin symbols
 * to reduce the number of individual store subscriptions.
 *
 * This is designed to be used at a parent component level where one
 * subscription can serve multiple CoinTag components.
 */
const usePriceData = (symbols: string[]): CoinPriceData => {
  const uniqueSymbols = useMemo(() => {
    return [...new Set(symbols)];
  }, [symbols]);

  // Access the price store once for all symbols
  const priceStore = usePriceStore();

  // Build a map of symbols to their price data
  const priceDataMap = useMemo<CoinPriceData>(() => {
    if (!uniqueSymbols.length) return {};

    // Create a map that collects all price data from a single store access
    return uniqueSymbols.reduce<CoinPriceData>((acc, symbol) => {
      const storePrice = priceStore.getPrice(symbol);

      acc[symbol] = {
        price: storePrice?.price,
        changePercent: storePrice?.changePercent,
      };

      return acc;
    }, {});
  }, [uniqueSymbols, priceStore]);

  return priceDataMap;
};

export default usePriceData;

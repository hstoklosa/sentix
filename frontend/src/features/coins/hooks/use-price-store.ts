import { create } from "zustand";

type TokenPrice = {
  symbol: string;
  price: number;
  changePercent: number;
  lastUpdated: number;
};

type TokenPriceStore = {
  prices: Record<string, TokenPrice>;
  getPrice: (symbol: string) => TokenPrice | null;
  updatePrice: (symbol: string, price: number, changePercent: number) => void;
};

/**
 * Normalise a symbol by removing the USDT suffix and converting to * uppercase
 *
 * @param symbol - The symbol to normalise
 * @returns The normalised symbol
 */
const normaliseSymbol = (symbol: string): string => {
  return symbol.replace(/usdt$/i, "").toUpperCase();
};

export const usePriceStore = create<TokenPriceStore>((set, get) => ({
  prices: {},

  getPrice: (symbol) => {
    if (!symbol) return null;

    const normalisedSymbol = normaliseSymbol(symbol);
    const price = get().prices[normalisedSymbol];

    return price || null;
  },

  updatePrice: (symbol, price, changePercent) => {
    const normalisedSymbol = normaliseSymbol(symbol);

    // console.log(
    //   `[TokenPriceStore] Updating price for ${normalisedSymbol} (from ${symbol}): ${price} (${changePercent}%)`
    // );

    set((state) => ({
      prices: {
        ...state.prices,
        [normalisedSymbol]: {
          symbol: normalisedSymbol,
          price,
          changePercent,
          lastUpdated: Date.now(),
        },
      },
    }));
  },
}));

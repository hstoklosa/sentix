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

export const usePriceStore = create<TokenPriceStore>((set, get) => ({
  prices: {},

  getPrice: (symbol) => {
    if (!symbol) return null;

    const upperSymbol = symbol.toUpperCase();
    const price = get().prices[upperSymbol];
    return price || null;
  },

  updatePrice: (symbol, price, changePercent) => {
    const upperSymbol = symbol.toUpperCase();

    console.log(
      `[TokenPriceStore] Updating price for ${upperSymbol}: ${price} (${changePercent}%)`
    );

    set((state) => ({
      prices: {
        ...state.prices,
        [upperSymbol]: {
          symbol: upperSymbol,
          price,
          changePercent,
          lastUpdated: Date.now(),
        },
      },
    }));
  },
}));

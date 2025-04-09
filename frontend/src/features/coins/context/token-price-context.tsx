import React, { createContext, useContext, useState, ReactNode } from "react";

type TokenPriceContextType = {
  tokenPrices: Record<string, { price: number; changePercent: number }>;
  addOrUpdatePrice: (symbol: string, price: number, changePercent: number) => void;
};

const TokenPriceContext = createContext<TokenPriceContextType | undefined>(
  undefined
);

type TokenPriceProviderProps = {
  children: ReactNode;
};

export const TokenPriceProvider = ({ children }: TokenPriceProviderProps) => {
  const [tokenPrices, setTokenPrices] = useState<
    Record<string, { price: number; changePercent: number }>
  >({});

  const addOrUpdatePrice = (
    symbol: string,
    price: number,
    changePercent: number
  ) => {
    setTokenPrices((prev) => ({
      ...prev,
      [symbol]: { price, changePercent },
    }));
  };

  return (
    <TokenPriceContext.Provider value={{ tokenPrices, addOrUpdatePrice }}>
      {children}
    </TokenPriceContext.Provider>
  );
};

export const useTokenPrice = () => {
  const context = useContext(TokenPriceContext);

  if (context === undefined) {
    throw new Error("useTokenPrice must be used within a TokenPriceProvider");
  }

  return context;
};

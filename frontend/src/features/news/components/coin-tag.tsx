import { useMemo } from "react";

import { cn } from "@/lib/utils";
import { usePriceStore } from "@/features/coins/hooks/use-price-store";

type CoinTagProps = {
  symbol: string;
};

/**
 * Displays a cryptocurrency tag with live price information.
 *
 * Purely a presentational component that reads from the global
 * price store and uses useMemo to prevent unnecessary re-renders
 * when parent components change.
 */
const CoinTag = ({ symbol }: CoinTagProps) => {
  const tokenPrice = usePriceStore((state) => state.getPrice(symbol));
  const changePercent = tokenPrice?.changePercent;

  // Memoize the rendered tag to prevent unnecessary re-renders
  return useMemo(
    () => (
      <span
        className={cn(
          "px-1.5 py-0.5 bg-secondary text-xs rounded-full",
          typeof changePercent === "number" &&
            changePercent > 0 &&
            "text-chart-2 bg-chart-2/10",
          typeof changePercent === "number" &&
            changePercent < 0 &&
            "text-destructive bg-destructive/10"
        )}
      >
        {symbol}
        {typeof changePercent === "number" &&
          ` (${changePercent > 0 ? "+" : ""}${changePercent.toFixed(2)}%)`}
      </span>
    ),
    [symbol, changePercent]
  );
};

export default CoinTag;

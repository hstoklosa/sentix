import { useMemo } from "react";

import { cn } from "@/lib/utils";

type CoinTagProps = {
  symbol: string;
  priceUsd?: number;
  priceTimestamp?: string;
  // New props for parent-provided price data
  currentPrice?: number;
  changePercent?: number;
};

const CoinTag = ({
  symbol,
  priceUsd,
  priceTimestamp,
  currentPrice,
  changePercent,
}: CoinTagProps) => {
  const hasProvidedPrice = typeof priceUsd === "number";
  const hasCurrentPrice = typeof currentPrice === "number";

  // Calculate price delta between article time and current price
  const viewData = useMemo(() => {
    let priceDelta = null;
    if (hasProvidedPrice && hasCurrentPrice && priceUsd !== 0) {
      const absoluteDelta = currentPrice - priceUsd;
      const percentDelta = (absoluteDelta / priceUsd) * 100;
      priceDelta = {
        percent: percentDelta,
        increased: percentDelta > 0,
      };
    }

    // Determine text content for the percentage display
    let percentText = "";
    if (priceDelta) {
      percentText = ` (${priceDelta.increased ? "+" : ""}${priceDelta.percent.toFixed(2)}%)`;
    } else if (typeof changePercent === "number") {
      percentText = ` (${changePercent > 0 ? "+" : ""}${changePercent.toFixed(2)}%)`;
    }

    // Determine styling based on price movement
    let colorClasses = "";
    if (priceDelta) {
      colorClasses = priceDelta.increased
        ? "text-chart-2 bg-chart-2/10"
        : "text-destructive bg-destructive/10";
    } else if (typeof changePercent === "number") {
      colorClasses =
        changePercent > 0
          ? "text-chart-2 bg-chart-2/10"
          : "text-destructive bg-destructive/10";
    }

    // Format tooltip content
    let tooltipContent;
    if (hasProvidedPrice && priceTimestamp && hasCurrentPrice) {
      const publishTime = new Date(priceTimestamp).toLocaleString();
      const baseTooltip = `Price at article time: $${priceUsd!.toFixed(2)} (${publishTime})`;

      if (priceDelta) {
        const currentPriceText = `Current price: $${currentPrice.toFixed(2)}`;
        const deltaText = `Delta: ${priceDelta.increased ? "+" : ""}${priceDelta.percent.toFixed(2)}%`;
        tooltipContent = `${baseTooltip}\n${currentPriceText}\n${deltaText}`;
      } else {
        tooltipContent = baseTooltip;
      }
    }

    return { priceDelta, percentText, colorClasses, tooltipContent };
  }, [
    hasProvidedPrice,
    hasCurrentPrice,
    priceUsd,
    currentPrice,
    priceTimestamp,
    changePercent,
  ]);

  return (
    <span
      className={cn(
        "px-1.5 py-0.5 bg-secondary text-xs rounded-full",
        viewData.colorClasses
      )}
      title={viewData.tooltipContent}
    >
      {symbol}
      {viewData.percentText}
    </span>
  );
};

export default CoinTag;

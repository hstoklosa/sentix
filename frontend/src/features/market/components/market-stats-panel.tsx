import { AlertCircle } from "lucide-react";

import { Spinner } from "@/components/ui/spinner";
import { formatCompactNumber } from "@/utils/format";

import { useGetStats } from "../api";
import PriceChangeTag from "./price-change-tag";

const MarketStatsPanel = () => {
  const { data: marketStats, isLoading, isError } = useGetStats();

  if (isLoading) {
    return <Spinner className="h-full w-full" />;
  }

  if (isError || !marketStats) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive flex items-center justify-center gap-2">
          <AlertCircle className="size-6" />
          Failed to load market stats
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 h-[53px] px-2.5 py-2 border-b border-border">
        <h2 className="text-md font-semibold">Market Stats</h2>
      </div>
      <div className="flex flex-col justify-center h-full gap-7.5 p-2.5">
        <div className="flex flex-col gap-1">
          <div className="flex justify-between gap-1">
            {/* Total Market Cap */}
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-muted-foreground">
                Market Cap
              </p>
              <div className="flex flex-row items-center gap-2">
                <p className="text-lg">
                  {formatCompactNumber(marketStats.total_market_cap, 2, "$", true)}
                </p>
                <PriceChangeTag
                  changePercent={marketStats.total_market_cap_24h_change}
                />
              </div>
            </div>

            {/* Total Volume */}
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-muted-foreground">
                Volume 24h
              </p>
              <div className="flex flex-row items-center gap-2">
                <p className="text-lg">
                  {formatCompactNumber(marketStats.total_volume_24h, 2, "$", true)}
                </p>
                <PriceChangeTag
                  changePercent={marketStats.total_volume_24h_change}
                />
              </div>
            </div>

            {/* BTC Dominance */}
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-muted-foreground">BTC Dom</p>
              <div className="flex flex-row items-center gap-2">
                <p className="text-lg">{marketStats.btc_dominance.toFixed(1)}%</p>
                <PriceChangeTag
                  changePercent={marketStats.btc_dominance_24h_change}
                />
              </div>
            </div>

            {/* ETH Dominance */}
            <div className="flex flex-col gap-1">
              <p className="text-sm font-medium text-muted-foreground">ETH Dom</p>
              <div className="flex flex-row items-center gap-2">
                <p className="text-lg">{marketStats.eth_dominance.toFixed(1)}%</p>
                <PriceChangeTag
                  changePercent={marketStats.eth_dominance_24h_change}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          {/* Fear & Greed Index */}
          <div className="flex flex-col gap-1 w-[25%]">
            <p className="text-sm font-medium text-muted-foreground">
              Fear & Greed Index
            </p>
            <div className="flex items-center gap-2">
              <FearAndGreedMeter value={marketStats.fear_and_greed_index} />
              <p className="text-xl">{marketStats.fear_and_greed_index}</p>
              <FearAndGreedIndicator value={marketStats.fear_and_greed_index} />
            </div>
          </div>

          {/* Sentiment */}
          <div className="flex flex-col gap-1 w-[25%]">
            <p className="text-sm font-medium text-muted-foreground">Sentiment</p>
            <div className="flex items-center gap-2">
              <FearAndGreedMeter value={marketStats.fear_and_greed_index} />
              <p className="text-xl">{marketStats.fear_and_greed_index}</p>
              <FearAndGreedIndicator value={marketStats.fear_and_greed_index} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

type FearAndGreedIndicatorProps = {
  value: number;
};

const FearAndGreedIndicator = ({ value }: FearAndGreedIndicatorProps) => {
  let label = "Neutral";
  let color = "text-muted-foreground";

  if (value >= 75) {
    label = "Extreme Greed";
    color = "text-chart-2";
  } else if (value >= 55) {
    label = "Greed";
    color = "text-chart-2/80";
  } else if (value >= 45) {
    label = "Neutral";
    color = "text-muted-foreground";
  } else if (value >= 25) {
    label = "Fear";
    color = "text-destructive/80";
  } else {
    label = "Extreme Fear";
    color = "text-destructive";
  }

  return <span className={`text-sm ${color}`}>{label}</span>;
};

// Add a visual meter for Fear & Greed Index
const FearAndGreedMeter = ({ value }: { value: number }) => {
  let bgColor = "bg-muted-foreground";

  if (value >= 75) {
    bgColor = "bg-chart-2";
  } else if (value >= 55) {
    bgColor = "bg-chart-2/80";
  } else if (value >= 45) {
    bgColor = "bg-muted";
  } else if (value >= 25) {
    bgColor = "bg-destructive/80";
  } else {
    bgColor = "bg-destructive";
  }

  return (
    <div className="w-16 h-3 bg-secondary rounded-full overflow-hidden">
      <div
        className={`h-full ${bgColor} rounded-full`}
        style={{ width: `${value}%` }}
      />
    </div>
  );
};

export default MarketStatsPanel;

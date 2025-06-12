import { AlertCircle } from "lucide-react";

import { Spinner } from "@/components/ui/spinner";
import { formatCompactNumber } from "@/utils/format";
import { SentimentTag } from "@/features/news/components";

import { useGetStats } from "../api";
import PriceChangeTag from "./price-change-tag";
import { FearGreedIndicator, FearGreedMeter } from "./fear-greed-index";

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
      <div className="flex items-center h-[55px] px-2.5 py-2 border-b border-border">
        <h2 className="text-md font-semibold">Market Stats</h2>
      </div>
      <div className="h-full grid grid-cols-4 grid-rows-2 gap-5 p-2.5 overflow-auto">
        <div className="row-start-1 row-end-2 col-start-1 col-end-2">
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-muted-foreground">Market Cap</p>
            <div className="flex flex-row items-center gap-2">
              <p className="text-md">
                {formatCompactNumber(marketStats.total_market_cap, 2, "$", true)}
              </p>
              <PriceChangeTag
                changePercent={marketStats.total_market_cap_24h_change}
              />
            </div>
          </div>
        </div>

        <div className="row-start-1 row-end-2 col-start-2 col-end-3">
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-muted-foreground">Volume 24h</p>
            <div className="flex flex-row items-center gap-2">
              <p className="text-md">
                {formatCompactNumber(marketStats.total_volume_24h, 2, "$", true)}
              </p>
              <PriceChangeTag changePercent={marketStats.total_volume_24h_change} />
            </div>
          </div>
        </div>

        <div className="row-start-1 row-end-2 col-start-3 col-end-4">
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-muted-foreground">BTC Dom</p>
            <div className="flex flex-row items-center gap-2">
              <p className="text-md">{marketStats.btc_dominance.toFixed(1)}%</p>
              <PriceChangeTag
                changePercent={marketStats.btc_dominance_24h_change}
              />
            </div>
          </div>
        </div>

        <div className="row-start-1 row-end-2 col-start-4 col-end-5">
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-muted-foreground">ETH Dom</p>
            <div className="flex flex-row items-center gap-2">
              <p className="text-md">{marketStats.eth_dominance.toFixed(1)}%</p>
              <PriceChangeTag
                changePercent={marketStats.eth_dominance_24h_change}
              />
            </div>
          </div>
        </div>

        <div className="row-start-2 row-end-3 col-start-1 col-end-2">
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-muted-foreground">Sentiment</p>
            <div className="flex items-center gap-2">
              <SentimentTag
                size="lg"
                sentiment={marketStats.market_sentiment}
              />
              <p className="text-md">{marketStats.market_sentiment}</p>
            </div>
          </div>
        </div>

        <div className="row-start-2 row-end-3 col-start-2 col-end-4">
          <div className="flex flex-col gap-1">
            <p className="text-sm font-medium text-muted-foreground">
              Fear & Greed Index
            </p>
            <div className="flex items-center gap-2">
              <FearGreedMeter value={marketStats.fear_and_greed_index} />
              <p className="text-md">{marketStats.fear_and_greed_index}</p>
              <FearGreedIndicator value={marketStats.fear_and_greed_index} />
            </div>
          </div>
        </div>

        {/* <div className="row-start-2 row-end-3 col-start-4 col-end-5">8</div> */}
      </div>
    </div>
  );
};

export default MarketStatsPanel;

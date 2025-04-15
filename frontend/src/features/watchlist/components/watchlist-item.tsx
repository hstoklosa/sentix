import { TrendingUp, TrendingDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { WatchlistCoin } from "../types";

const WatchlistItem = ({ coin }: { coin: WatchlistCoin }) => {
  const priceChangeIsPositive = (coin.price_change_percentage_24h || 0) > 0;
  const priceChangeIsNegative = (coin.price_change_percentage_24h || 0) < 0;

  const formatPrice = (price: number): string => {
    if (price < 0.001) return price.toFixed(6);
    if (price < 1) return price.toFixed(4);
    if (price < 10) return price.toFixed(2);
    return price.toLocaleString("en-US", { maximumFractionDigits: 2 });
  };

  const formatMarketCap = (marketCap: number): string => {
    if (marketCap >= 1e12) return `${(marketCap / 1e12).toFixed(2)}T`;
    if (marketCap >= 1e9) return `${(marketCap / 1e9).toFixed(2)}B`;
    if (marketCap >= 1e6) return `${(marketCap / 1e6).toFixed(2)}M`;
    return marketCap.toLocaleString();
  };

  return (
    <div className="px-3 py-2 border-b border-border hover:bg-muted/30 transition-colors">
      <div className="flex items-center">
        {/* Coin info */}
        <div className="flex items-center gap-2.5 w-[50%]">
          <img
            src={coin.image}
            alt={coin.name}
            className="size-4.5 rounded-full"
          />
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm">{coin.name}</span>
              <span className="text-[10px] text-muted-foreground uppercase">
                {coin.symbol}
              </span>
            </div>
          </div>
        </div>

        {/* Price */}
        <div className="w-[20%] text-sm">${formatPrice(coin.current_price)}</div>

        {/* Change */}
        <div
          className={cn(
            "w-[20%] flex items-center text-sm",
            priceChangeIsPositive
              ? "text-emerald-500"
              : priceChangeIsNegative
                ? "text-rose-500"
                : "text-muted-foreground"
          )}
        >
          {/* {priceChangeIsPositive && (
            <TrendingUp
              size={12}
              className="mr-1"
            />
          )}
          {priceChangeIsNegative && (
            <TrendingDown
              size={12}
              className="mr-1"
            />
          )} */}
          {coin.price_change_percentage_24h
            ? `${priceChangeIsPositive ? "+" : ""}${coin.price_change_percentage_24h.toFixed(2)}%`
            : "0.00%"}
        </div>

        {/* Market Cap */}
        <div className="w-[10%] text-muted-foreground text-sm">
          {formatMarketCap(coin.market_cap)}
        </div>
      </div>
    </div>
  );
};

export default WatchlistItem;

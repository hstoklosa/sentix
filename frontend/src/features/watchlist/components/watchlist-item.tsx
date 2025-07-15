import { useNavigate } from "@tanstack/react-router";

import { cn } from "@/lib/utils";
import { WatchlistCoin } from "../types";

const WatchlistItem = ({ coin }: { coin: WatchlistCoin }) => {
  const navigate = useNavigate();
  const priceChangeIsPositive = (coin.price_change_percentage_24h || 0) > 0;
  const priceChangeIsNegative = (coin.price_change_percentage_24h || 0) < 0;

  const handleClick = () => {
    navigate({
      to: "/dashboard",
      search: (prev) => ({
        ...prev,
        coin: coin.symbol.toUpperCase(),
      }),
    });
  };

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
    <div
      className="px-3 py-2 border-b border-border hover:bg-muted/30 transition-colors cursor-pointer"
      onClick={handleClick}
    >
      <div className="flex items-center">
        {/* Coin info */}
        <div className="flex items-center gap-2.5 w-[59%]">
          <img
            src={coin.image}
            alt={coin.name}
            className="size-4.5 rounded-full"
          />
          <div className="flex-1 min-w-0 mr-10">
            <div className="flex items-center gap-1.5">
              {/* className="text-sm max-w-28 min-[640px]:max-w-32 min-[768px]:max-w-40 min-[1024px]:max-w-48 min-[1280px]:max-w-56 truncate" */}
              <span
                className="text-sm truncate"
                title={coin.name}
              >
                {coin.name}
              </span>
              <span className="text-[10px] text-muted-foreground uppercase shrink-0">
                {coin.symbol}
              </span>
            </div>
          </div>
        </div>

        {/* Price */}
        <div className="w-[16%] text-sm">${formatPrice(coin.current_price)}</div>

        {/* Change */}
        <div
          className={cn(
            "w-[15%] flex items-center text-sm",
            priceChangeIsPositive
              ? "text-chart-2"
              : priceChangeIsNegative
                ? "text-destructive"
                : "text-muted-foreground"
          )}
        >
          {coin.price_change_percentage_24h
            ? `${priceChangeIsPositive ? "+" : ""}${coin.price_change_percentage_24h.toFixed(2)}%`
            : "0.00%"}
        </div>

        {/* Market Cap */}
        {/* text-muted-foreground */}
        <div className="w-[10%] text-sm">{formatMarketCap(coin.market_cap)}</div>
      </div>
    </div>
  );
};

export default WatchlistItem;

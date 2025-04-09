import { cn } from "@/lib/utils";
import { useTokenPrice } from "@/features/coins/hooks/use-token-price";

type CoinTagProps = {
  symbol: string;
};

const CoinTag = ({ symbol }: CoinTagProps) => {
  const { price, changePercent } = useTokenPrice(symbol) ?? {};

  return (
    <span
      className={cn(
        "px-1.5 py-0.5 bg-secondary text-xs rounded-full",
        changePercent && changePercent > 0 && "text-chart-2 bg-chart-2/10",
        changePercent && changePercent < 0 && "text-destructive bg-destructive/10"
      )}
    >
      {symbol}
      {changePercent &&
        ` (${changePercent > 0 ? "+" : ""}${changePercent.toFixed(2)}%)`}
    </span>
  );
};

export default CoinTag;

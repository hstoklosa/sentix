import { ArrowDownIcon, ArrowUpIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type PriceChangeTagProps = {
  changePercent: number;
};

const PriceChangeTag = ({ changePercent }: PriceChangeTagProps) => {
  const isPositive = typeof changePercent === "number" && changePercent > 0;
  const isNegative = typeof changePercent === "number" && changePercent < 0;

  return (
    <span
      className={cn(
        "px-1.5 py-0.5 bg-secondary text-xs rounded-full flex items-center gap-0.5",
        isPositive && "text-chart-2 bg-chart-2/10",
        isNegative && "text-destructive bg-destructive/10"
      )}
    >
      {isPositive && <ArrowUpIcon className="size-3" />}
      {isNegative && <ArrowDownIcon className="size-3" />}
      {typeof changePercent === "number" &&
        `${isPositive ? "" : ""}${Math.abs(changePercent).toFixed(2)}%`}
    </span>
  );
};

export default PriceChangeTag;

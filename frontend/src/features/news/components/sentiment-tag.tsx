import { useMemo } from "react";
import { Frown, Meh, Smile } from "lucide-react";

import { cn } from "@/lib/utils";

type SentimentTagProps = {
  className?: string;
  iconSize?: number;
  sentiment: string;
};

const SentimentTag = ({
  sentiment,
  className,
  iconSize = 4,
}: SentimentTagProps) => {
  const icon = useMemo(() => {
    const normalisedSentiment = sentiment?.toLowerCase() || "";

    switch (true) {
      case normalisedSentiment.includes("bullish"):
        return <Smile className={cn("text-chart-2", `size-${iconSize}`)} />;
      case normalisedSentiment.includes("bearish"):
        return <Frown className={cn("text-destructive", `size-${iconSize}`)} />;
      default:
        return <Meh className={cn("text-muted-foreground", `size-${iconSize}`)} />;
    }
  }, [sentiment]);

  return (
    <div
      className={cn("flex items-center gap-1 text-sm", className)}
      aria-hidden="true"
    >
      {icon}
    </div>
  );
};

export default SentimentTag;

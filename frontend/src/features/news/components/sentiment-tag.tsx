import { useMemo } from "react";
import { Frown, Meh, Smile } from "lucide-react";

import { cn } from "@/lib/utils";

type SentimentTagProps = {
  className?: string;
  sentiment: string;
  score: number;
};

const SentimentTag = ({ sentiment, score, className }: SentimentTagProps) => {
  const icon = useMemo(() => {
    const normalisedSentiment = sentiment?.toLowerCase() || "";

    switch (true) {
      case normalisedSentiment.includes("bullish"):
        return <Smile className="size-4 text-chart-2" />;
      case normalisedSentiment.includes("bearish"):
        return <Frown className="size-4 text-destructive" />;
      default:
        return <Meh className="size-4 text-muted-foreground" />;
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

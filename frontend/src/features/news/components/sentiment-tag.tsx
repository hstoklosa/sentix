import { useMemo } from "react";
import { Frown, Meh, Smile } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const sentimentIconVariants = cva("", {
  variants: {
    size: {
      sm: "size-3",
      md: "size-4",
      lg: "size-5",
      xl: "size-6",
    },
  },
  defaultVariants: {
    size: "md",
  },
});

type SentimentTagProps = {
  className?: string;
  sentiment: string;
} & VariantProps<typeof sentimentIconVariants>;

const SentimentTag = ({ sentiment, className, size }: SentimentTagProps) => {
  const icon = useMemo(() => {
    const normalisedSentiment = sentiment?.toLowerCase() || "";
    const iconClass = sentimentIconVariants({ size });

    switch (true) {
      case normalisedSentiment.includes("bullish"):
        return <Smile className={cn("text-chart-2", iconClass)} />;
      case normalisedSentiment.includes("bearish"):
        return <Frown className={cn("text-destructive", iconClass)} />;
      default:
        return <Meh className={cn("text-muted-foreground", iconClass)} />;
    }
  }, [sentiment, size]);

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

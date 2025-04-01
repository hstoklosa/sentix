import { useMemo, useRef } from "react";
import { ExternalLink } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatRelativeTime } from "@/utils/format";

import { NewsItem as NewsItemType } from "@/features/news/types";

type NewsItemProps = {
  news: NewsItemType;
  refreshCounter?: number; // optional for backward compatibility
};

/**
 * Determines if the time should be recalculated based on
 *  - item age
 *  - refresh counter
 */
const shouldRecalculateTime = (timestamp: string, counter: number = 0): boolean => {
  if (!counter) return true; // Always calculate on first render

  const now = Date.now();
  const date = new Date(timestamp).getTime();
  const ageInSeconds = Math.floor((now - date) / 1000);

  // Define adaptive refresh rates based on item age
  if (ageInSeconds < 60) {
    // Less than 1 minute: update every refresh (5s)
    return true;
  } else if (ageInSeconds < 300) {
    // 1-5 minutes: update every 10s (every 2 refreshes)
    return counter % 2 === 0;
  } else if (ageInSeconds < 1800) {
    // 5-30 minutes: update every 30s (every 6 refreshes)
    return counter % 6 === 0;
  } else {
    // Older than 30 minutes: update every 60s (every 12 refreshes)
    return counter % 12 === 0;
  }
};

const NewsItem = ({ news, refreshCounter = 0 }: NewsItemProps) => {
  const lastTimeRef = useRef<string | null>(null);

  const relativeTime = useMemo(() => {
    if (!lastTimeRef.current || shouldRecalculateTime(news.time, refreshCounter)) {
      const newTime = formatRelativeTime(news.time);
      lastTimeRef.current = newTime;
      return newTime;
    }

    return lastTimeRef.current;
  }, [news.time, refreshCounter]);

  return (
    <div className="border border-border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow relative group">
      <div className="flex items-start gap-3">
        <div className="w-12">
          <span
            className="text-xs text-muted-foreground whitespace-nowrap mt-1"
            title={news.time}
          >
            {relativeTime}
          </span>
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-sm mb-2">{news.title}</h3>
          {/* <p className="text-sm text-muted-foreground mb-3">{news.body}</p> */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1">
              {news.icon && (
                <img
                  src={news.icon}
                  alt={news.source}
                  className="w-4 h-4 rounded-full"
                />
              )}
              <span className="text-xs text-muted-foreground">{news.source}</span>
            </div>

            {news.coins && news.coins.length > 0 && (
              <>
                <span className="text-xs text-muted-foreground">|</span>
                {news.coins.map((coin) => (
                  <span
                    key={coin}
                    className="px-2 py-1 bg-secondary text-xs rounded-full"
                  >
                    {coin}
                  </span>
                ))}
              </>
            )}
          </div>
          {/* <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-muted-foreground">{news.feed}</span>
          </div> */}
        </div>
      </div>
    </div>
  );
};

export default NewsItem;

import { useMemo, useRef } from "react";
import { ExternalLink, Link as LinkIcon, Copy } from "lucide-react";
import { Link } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { formatRelativeTime } from "@/utils/format";

import { NewsItem as NewsItemType } from "@/features/news/types";

type NewsItemProps = {
  news: NewsItemType;
  refreshCounter?: number; // optional for backward compatibility
};

/*
 * Determines if the time should be recalculated
 * based on item age and refresh counter.
 */
const shouldRecalculateTime = (timestamp: string, counter: number = 0): boolean => {
  if (!counter) return true; // Always calculate on first render

  const now = Date.now();
  const date = new Date(timestamp).getTime();
  const ageInSeconds = Math.floor((now - date) / 1000);

  // Define adaptive refresh rates based on item age
  switch (true) {
    case ageInSeconds < 60: // Less 1 minute: update every refresh (5s)
      return true;
    case ageInSeconds < 300: // 1-5 minutes: update every 10s (every 2 refreshes)
      return counter % 2 === 0;
    case ageInSeconds < 1800: // 5-30 minutes: update every 30s (every 6 refreshes)
      return counter % 6 === 0;
    default: // Older than 30 minutes: update every 60s (every 12 refreshes)
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

  const handleCopyUrl = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(news.url).catch((error) => {
      console.error("Failed to copy URL:", error);
    });
  };

  const handleCopyTitle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(news.title).catch((error) => {
      console.error("Failed to copy title:", error);
    });
  };

  return (
    <Link
      to=""
      className="group relative block p-2.5 border-b border-border hover:bg-muted/50 transition-colors"
    >
      <div className="flex items-start gap-3">
        <div className="inline-flex w-10">
          <span
            className="text-xs pt-[1px] text-muted-foreground whitespace-nowrap"
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

      <div
        className="absolute top-2 right-2 flex gap-3.5 opacity-0 group-hover:opacity-100 transition-opacity rounded-md bg-background shadow-sm py-1 px-3 border border-border"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={handleCopyTitle}
          className="size-4 flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          aria-label="Copy Title"
        >
          <Copy className="size-4" />
        </button>

        <button
          onClick={handleCopyUrl}
          className="size-4 flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          aria-label="Copy URL"
        >
          <LinkIcon className="size-4" />
        </button>

        <a
          href={news.url}
          target="_blank"
          rel="noopener noreferrer"
          className="size-4 flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          aria-label="Read more"
        >
          <ExternalLink className="size-4" />
        </a>
      </div>
    </Link>
  );
};

export default NewsItem;

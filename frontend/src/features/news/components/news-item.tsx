import { useMemo, useRef } from "react";
import { ExternalLink, Link as LinkIcon, Copy } from "lucide-react";
import { Link } from "@tanstack/react-router";

import { formatRelativeTime } from "@/utils/format";

import { NewsItem as NewsItemType } from "@/features/news/types";

type NewsItemProps = {
  news: NewsItemType;
  refreshCounter?: number;
};

/**
 * Determines if the relative time display should be recalculated based on item age and refresh counter.
 *
 * Implements an adaptive refresh strategy:
 * - For items less than 1 minute old: updates every refresh cycle (5s)
 * - For items 1-5 minutes old: updates every 2 refresh cycles (10s)
 * - For items 5-30 minutes old: updates every 6 refresh cycles (30s)
 * - For items older than 30 minutes: updates every 12 refresh cycles (60s)
 *
 * @param timestamp - The ISO timestamp string of the news item
 * @param counter - The current refresh counter (increments with each refresh cycle)
 * @returns Boolean indicating whether the time should be recalculated
 */
const shouldRecalculateTime = (timestamp: string, counter: number = 0): boolean => {
  if (!counter) return true; // always recalculate on first render (counter = 0)

  const now = Date.now();
  const date = new Date(timestamp).getTime();
  const ageInSeconds = Math.floor((now - date) / 1000);

  switch (true) {
    case ageInSeconds < 60:
      return true;
    case ageInSeconds < 300:
      return counter % 2 === 0;
    case ageInSeconds < 1800:
      return counter % 6 === 0;
    default:
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

  const handleCopy = (text: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(text).catch((error) => {
      console.error(`Failed to copy: ${error}`);
    });
  };

  // Common button class for action buttons
  const actionButtonClass =
    "size-4 flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

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
        className="absolute top-1 right-1 flex gap-2.5 opacity-0 group-hover:opacity-100 transition-opacity rounded-md bg-background shadow-sm py-1 px-2.5 border border-border"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          aria-label="Copy Title"
          className={actionButtonClass}
          onClick={(e) => handleCopy(news.title, e)}
        >
          <Copy className="size-3.5" />
        </button>
        <button
          aria-label="Copy URL"
          className={actionButtonClass}
          onClick={(e) => handleCopy(news.url, e)}
        >
          <LinkIcon className="size-3.5" />
        </button>
        <a
          aria-label="Read more"
          href={news.url}
          target="_blank"
          className={actionButtonClass}
          rel="noopener noreferrer"
        >
          <ExternalLink className="size-3.5" />
        </a>
      </div>
    </Link>
  );
};

export default NewsItem;

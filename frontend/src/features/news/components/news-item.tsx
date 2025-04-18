import { useMemo, useRef } from "react";
import { Link } from "@tanstack/react-router";
import { toast } from "sonner";
import { ExternalLink, Link as LinkIcon, Copy, Bookmark } from "lucide-react";

import xIcon from "@/assets/x.png";
import newsIcon from "@/assets/news.png";
import { cn } from "@/lib/utils";
import { formatRelativeTime, formatDateTime } from "@/utils/format";

import CoinTag from "@/features/news/components/coin-tag";
import SentimentTag from "@/features/news/components/sentiment-tag";
import { NewsItem as NewsItemType } from "@/features/news/types";
import { useCreateBookmark } from "@/features/bookmarks/api/create-bookmark";
import { useDeleteBookmark } from "@/features/bookmarks/api/delete-bookmark";

type NewsItemProps = {
  news: NewsItemType;
  refreshCounter?: number;
};

/**
 * Determines if the relative time display should be recalculated based on
 * item age and refresh counter (implementing an adaptive refresh strategy).
 */
const shouldRecalculateTime = (timestamp: string, counter: number = 0): boolean => {
  if (!counter) return true; // always recalculate on first render (counter = 0)

  const now = Date.now();
  const date = new Date(timestamp).getTime();
  const ageInSeconds = Math.floor((now - date) / 1000);

  switch (true) {
    // less than 1 minute old: updates every refresh cycle (5s)
    case ageInSeconds < 60:
      return true;
    // 1-5 minutes old: updates every 2 refresh cycles (10s)
    case ageInSeconds < 300:
      return counter % 2 === 0;
    // 5-30 minutes old: updates every 6 refresh cycles (30s)
    case ageInSeconds < 1800:
      return counter % 6 === 0;
    // older than 30 minutes: updates every 12 refresh cycles (60s)
    default:
      return counter % 12 === 0;
  }
};

const NewsItem = ({ news, refreshCounter = 0 }: NewsItemProps) => {
  const lastTimeRef = useRef<string | null>(null);

  const createBookmark = useCreateBookmark({
    onSuccess: () => toast.success("The post has been added to bookmarks"),
    onError: () => toast.error("Failed to bookmark this post"),
  });
  const deleteBookmark = useDeleteBookmark({
    onSuccess: () => toast.success("The post has been removed from bookmarks"),
    onError: () => toast.error("Failed to remove this post from bookmarks"),
  });

  const relativeTime = useMemo(() => {
    if (!lastTimeRef.current || shouldRecalculateTime(news.time, refreshCounter)) {
      const newTime = formatRelativeTime(news.time);
      lastTimeRef.current = newTime;
      return newTime;
    }

    return lastTimeRef.current;
  }, [news.time, refreshCounter]);

  // Format the absolute time for tooltip display
  const formattedDateTime = useMemo(() => {
    return formatDateTime(news.time);
  }, [news.time]);

  const handleBookmarkToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    news.is_bookmarked
      ? deleteBookmark.mutate(news.id)
      : createBookmark.mutate({ news_item_id: news.id });
  };

  const actionButtonClass =
    "size-4 flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  const handleCopyTitle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard
      .writeText(news.title)
      .then(() => toast.success("The title has been copied to clipboard"))
      .catch(() => toast.error("Failed to copy title to clipboard"));
  };

  const handleCopyUrl = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard
      .writeText(news.url)
      .then(() => toast.success("The URL has been copied to clipboard"))
      .catch(() => toast.error("Failed to copy URL to clipboard"));
  };

  return (
    <Link
      to="/dashboard/$postId"
      params={{ postId: String(news.id) }}
      className="group relative block p-2.5 border-b border-border transition-colors [&.active]:bg-muted hover:bg-muted/50"
    >
      <div className="flex items-start gap-3">
        <div className="inline-flex w-10">
          <span
            className="text-xs pt-[1px] text-muted-foreground whitespace-nowrap cursor-help"
            title={formattedDateTime}
            aria-label={`Posted ${formattedDateTime}`}
          >
            {relativeTime}
          </span>
        </div>
        <div className="flex-1">
          <div className="flex items-start gap-1.5 mb-2">
            {news.icon_url && (
              <img
                src={news.icon_url}
                alt={news.source}
                className="size-4 rounded-full shrink-0 mt-0.5"
              />
            )}
            <h3 className="font-medium text-sm line-clamp-2 overflow-hidden text-ellipsis">
              {news.title}
              {news.source === "Twitter" && <span>: {news.body}</span>}
            </h3>
          </div>

          {/* <p className="text-sm text-muted-foreground mb-3">{news.body}</p> */}

          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1">
              <div
                className={cn(
                  "flex justify-center items-center size-4 rounded-full bg-primary/10",
                  news.source === "Twitter" ? "bg-black" : "bg-[#7233F7]"
                )}
              >
                {news.source === "Twitter" ? (
                  <img
                    src={xIcon}
                    alt="X"
                    className="size-2.5"
                  />
                ) : (
                  <img
                    src={newsIcon}
                    alt="News"
                    className="w-2.5"
                  />
                )}
              </div>
              <span className="text-xs text-muted-foreground capitalize">
                {news.source}
              </span>
            </div>

            {news.coins && news.coins.length > 0 && (
              <>
                <span className="text-xs text-muted-foreground">|</span>
                {news.coins.map((coin) => (
                  <CoinTag
                    key={coin.id}
                    symbol={coin.symbol}
                  />
                ))}
              </>
            )}

            {/* TODO: Do not compute sentiment for news without related coins */}
            {news.coins.length > 0 &&
              news.sentiment &&
              news.score !== undefined && (
                <SentimentTag
                  className="ml-auto"
                  sentiment={news.sentiment}
                />
              )}
          </div>
        </div>
      </div>

      <div
        className="absolute top-1 right-1 flex gap-2.5 opacity-0 group-hover:opacity-100 transition-opacity rounded-md bg-background shadow-sm py-1 px-2.5 border border-border"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          aria-label={news.is_bookmarked ? "Remove bookmark" : "Add bookmark"}
          title={news.is_bookmarked ? "Remove bookmark" : "Add bookmark"}
          className={cn(actionButtonClass, news.is_bookmarked && "text-primary")}
          onClick={handleBookmarkToggle}
          // disabled={isLoading}
        >
          <Bookmark
            className="size-3.5"
            fill={news.is_bookmarked ? "currentColor" : "none"}
          />
        </button>
        <button
          aria-label="Copy Title"
          title="Copy Title"
          className={actionButtonClass}
          onClick={handleCopyTitle}
        >
          <Copy className="size-3.5" />
        </button>
        <button
          aria-label="Copy URL"
          title="Copy URL"
          className={actionButtonClass}
          onClick={handleCopyUrl}
        >
          <LinkIcon className="size-3.5" />
        </button>
        <a
          aria-label="Read more"
          title="Visit original source"
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

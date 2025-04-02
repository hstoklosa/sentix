import { useState, useEffect } from "react";
import { AlertCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";

import { useNewsWebSocket } from "../hooks";
import { NewsItem as NewsItemType } from "../types";

import NewsItem from "./news-item";

const NewsList = () => {
  const [newsItems, setNewsItems] = useState<NewsItemType[]>([]);
  const [refreshCounter, setRefreshCounter] = useState(0);
  const { isConnected, error } = useNewsWebSocket({
    onMessage: (news: NewsItemType) => {
      setNewsItems((prev) => [news, ...prev].slice(0, 100));
    },
  });

  // Update refresh counter every 5 seconds
  // to trigger relative time recalculation
  useEffect(() => {
    const interval = setInterval(() => {
      setRefreshCounter((count) => count + 1);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Determine content state
  const isLoading = !isConnected || newsItems.length === 0;
  const loadingMessage = !isConnected
    ? "Connecting to news feed..."
    : "Waiting for news updates...";

  return (
    <>
      <div className="p-2 border-b border-border">
        <h2 className="text-lg font-semibold flex items-center">
          <span
            className={cn(
              "inline-block w-2 h-2 rounded-full mr-2",
              isConnected ? "bg-chart-2" : "bg-destructive"
            )}
          />
          News Feed
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-destructive flex items-center justify-center gap-2">
              <AlertCircle className="size-6" />
              Connection has failed
            </p>
          </div>
        ) : isLoading ? (
          <div className="flex flex-row items-center justify-center h-full py-6 gap-3">
            <Spinner size="md" />
            <p className="text-muted-foreground">{loadingMessage}</p>
          </div>
        ) : (
          <div>
            {/* TODO: Add ids to news items and change key later */}
            {newsItems.map((item: NewsItemType, index: number) => (
              <NewsItem
                key={index}
                news={item}
                refreshCounter={refreshCounter}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
};

export default NewsList;

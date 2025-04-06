import { useState, useEffect } from "react";
import { AlertCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";

import NewsItem from "./news-item";
import { useGetNews, useUpdateNewsCache } from "../api";
import { useNewsWebSocket } from "../hooks";
import { NewsItem as NewsItemType } from "../types";

const NewsList = () => {
  const [refreshCounter, setRefreshCounter] = useState(0);

  const { data, isLoading, isError } = useGetNews();
  const updateNewsCache = useUpdateNewsCache();
  const { isConnected, error: websocketError } = useNewsWebSocket({
    onMessage: (news: NewsItemType) => updateNewsCache(news),
  });

  // Update refresh counter every 5 seconds to trigger
  // relative time recalculation
  useEffect(() => {
    const interval = setInterval(() => {
      setRefreshCounter((count) => count + 1);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadingMessage = !isConnected
    ? "Connecting to news feed..."
    : isLoading
      ? "Loading news..."
      : "Waiting for news updates...";

  console.log(data, isLoading, isError);

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
        {websocketError ||
          (isError && (
            <div className="flex items-center justify-center h-full">
              <p className="text-destructive flex items-center justify-center gap-2">
                <AlertCircle className="size-6" />
                {isError ? "Connection has failed" : "Failed to load news"}
              </p>
            </div>
          ))}
        {!isConnected || isLoading ? (
          <div className="flex flex-row items-center justify-center h-full py-6 gap-3">
            <Spinner size="md" />
            <p className="text-muted-foreground">{loadingMessage}</p>
          </div>
        ) : (
          <>
            {data?.items.map((item) => (
              <NewsItem
                key={item.id}
                news={item}
                refreshCounter={refreshCounter}
              />
            ))}
          </>
        )}
      </div>
    </>
  );
};

export default NewsList;

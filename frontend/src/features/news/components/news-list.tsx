import { useState, useEffect } from "react";

import { cn } from "@/lib/utils";

import { useNewsWebSocket } from "../hooks";
import { NewsItem as NewsItemType } from "../types";

import NewsItem from "./news-item";

const NewsList = () => {
  const [refreshCounter, setRefreshCounter] = useState(0);
  const [newsItems, setNewsItems] = useState<NewsItemType[]>([]);
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

  return (
    <>
      <div className="p-2 border-b border-border">
        <h2 className="text-lg font-semibold flex items-center">
          <span
            className={cn(
              "inline-block w-2 h-2 rounded-full mr-2",
              isConnected ? "bg-green-500" : "bg-red-500"
            )}
          ></span>
          News Feed
        </h2>

        {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
      </div>

      <div className="flex-1 rounded-lg overflow-y-auto">
        {newsItems.length === 0 ? (
          <p className="text-muted-foreground">Waiting for news updates...</p>
        ) : (
          <div className="">
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

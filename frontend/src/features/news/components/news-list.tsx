import { useState } from "react";

import { useNewsWebSocket } from "../hooks";
import { NewsItem as NewsItemType } from "../types";

import NewsItem from "./news-item";

const NewsList = () => {
  const [newsItems, setNewsItems] = useState<NewsItemType[]>([]);
  const { isConnected, error } = useNewsWebSocket({
    onMessage: (news: NewsItemType) => {
      setNewsItems((prev) => [news, ...prev].slice(0, 100));
    },
  });

  return (
    <>
      <div className="p-4 rounded-lg shadow mb-2">
        <h2 className="text-xl font-semibold mb-4">
          <span
            className={`inline-block w-2 h-2 rounded-full mr-2 ${
              isConnected ? "bg-green-500" : "bg-red-500"
            }`}
          ></span>
          News Feed
        </h2>

        {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
      </div>

      <div className="flex-1 p-4 rounded-lg shadow overflow-y-auto">
        {newsItems.length === 0 ? (
          <p className="text-muted-foreground">Waiting for news updates...</p>
        ) : (
          <div className="space-y-4">
            {/* TODO: Add ids to news items and change key later */}
            {newsItems.map((item: NewsItemType, index: number) => (
              <NewsItem
                key={index}
                news={item}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
};

export default NewsList;

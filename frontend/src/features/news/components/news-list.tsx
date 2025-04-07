import { useState, useEffect, useRef, useCallback } from "react";
import { AlertCircle } from "lucide-react";
import { useVirtualizer } from "@tanstack/react-virtual";

import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";

import NewsItem from "./news-item";
import { useGetInfinitePosts, useUpdatePostsCache } from "../api";
import { useNewsWebSocket } from "../hooks";
import { NewsItem as NewsItemType, NewsFeedResponse } from "../types";

const NewsList = () => {
  const [refreshCounter, setRefreshCounter] = useState(0);
  const parentRef = useRef<HTMLDivElement>(null);

  const {
    data,
    isLoading,
    isError,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
  } = useGetInfinitePosts();
  const { isConnected, error: isWebsocketError } = useNewsWebSocket({
    onMessage: (news: NewsItemType) => updatePostsCache(news),
  });
  const updatePostsCache = useUpdatePostsCache();

  // Flatten all news items from all pages
  const allNewsItems = data
    ? data.pages.flatMap((page: NewsFeedResponse) => page.items)
    : [];

  // Set up virtualizer for rendering only visible items with dynamic measurement
  const rowVirtualizer = useVirtualizer({
    count: hasNextPage ? allNewsItems.length + 1 : allNewsItems.length, // +1 for loading row
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // Initial estimate, will be refined by actual measurements
    overscan: 5,
    measureElement: useCallback((element: Element | null) => {
      // Get actual height of the element including margins
      if (!element) return 100;
      const rect = element.getBoundingClientRect();
      return rect.height;
    }, []),
  });

  // Load more items when user scrolls to bottom
  useEffect(() => {
    const [lastItem] = [...rowVirtualizer.getVirtualItems()].reverse();

    if (!lastItem) {
      return;
    }

    if (
      lastItem.index >= allNewsItems.length - 1 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  }, [
    hasNextPage,
    fetchNextPage,
    allNewsItems.length,
    isFetchingNextPage,
    rowVirtualizer.getVirtualItems(),
  ]);

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

  // console.log(data, isLoading, isError);

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

      {isError || isWebsocketError ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-destructive flex items-center justify-center gap-2">
            <AlertCircle className="size-6" />
            {isError ? "Connection has failed" : "Failed to load news"}
          </p>
        </div>
      ) : !isConnected || (isLoading && !allNewsItems.length) ? (
        <div className="flex flex-row items-center justify-center h-full py-6 gap-3">
          <Spinner size="md" />
          <p className="text-muted-foreground">{loadingMessage}</p>
        </div>
      ) : (
        <div
          ref={parentRef}
          className="flex-1 overflow-y-auto"
        >
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: "100%",
              position: "relative",
            }}
          >
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const isLoaderRow = virtualRow.index > allNewsItems.length - 1;
              const item = allNewsItems[virtualRow.index];

              return (
                <div
                  key={virtualRow.key}
                  data-index={virtualRow.index}
                  ref={rowVirtualizer.measureElement}
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    transform: `translateY(${virtualRow.start}px)`,
                  }}
                >
                  {isLoaderRow ? (
                    hasNextPage ? (
                      <div className="flex justify-center items-center py-4">
                        <Spinner size="sm" />
                        <span className="ml-2 text-muted-foreground">
                          Loading more news...
                        </span>
                      </div>
                    ) : (
                      <div className="text-center py-4 text-muted-foreground">
                        No more news to load
                      </div>
                    )
                  ) : (
                    <NewsItem
                      news={item}
                      refreshCounter={refreshCounter}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
};

export default NewsList;

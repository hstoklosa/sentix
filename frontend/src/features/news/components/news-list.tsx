import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { AlertCircle, ChevronDown } from "lucide-react";
import { useVirtualizer } from "@tanstack/react-virtual";

import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";
import { arraysHaveSameElements, setsAreEqual } from "@/utils/list";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import NewsItem from "./news-item";
import { useGetInfinitePosts, useUpdatePostsCache } from "../api";
import { useGetInfiniteBookmarkedPosts } from "@/features/bookmarks/api/get-bookmarks";
import { useWebSocketContext } from "../context";
import { NewsItem as NewsItemType, NewsFeedResponse } from "../types";
import { BookmarkedNewsResponse } from "@/features/bookmarks/types";
import useCoinSubscription from "@/features/coins/hooks/use-coin-subscription";

type FeedType = "all" | "bookmarked";

const NewsList = () => {
  const [feedType, setFeedType] = useState<FeedType>("all");
  const [refreshCounter, setRefreshCounter] = useState(0);
  const parentRef = useRef<HTMLDivElement>(null);
  const visibleItemsRef = useRef(new Set<number>());
  const lastSymbolsRef = useRef<string[]>([]);
  const updateDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const { subscribeToSymbols, unsubscribeFromSymbols } = useCoinSubscription();
  const { isConnected, error: isWebsocketError } = useWebSocketContext();

  // Query for all news posts
  const {
    data: allNewsData,
    isLoading: isAllNewsLoading,
    isError: isAllNewsError,
    isFetchingNextPage: isAllNewsFetchingNextPage,
    hasNextPage: hasAllNewsNextPage,
    fetchNextPage: fetchAllNewsNextPage,
  } = useGetInfinitePosts();

  // Query for bookmarked posts
  const {
    data: bookmarkedData,
    isLoading: isBookmarkedLoading,
    isError: isBookmarkedError,
    isFetchingNextPage: isBookmarkedFetchingNextPage,
    hasNextPage: hasBookmarkedNextPage,
    fetchNextPage: fetchBookmarkedNextPage,
  } = useGetInfiniteBookmarkedPosts();

  const updatePostsCache = useUpdatePostsCache();

  // Select the appropriate data based on feed type
  const data = feedType === "all" ? allNewsData : bookmarkedData;
  const isLoading = feedType === "all" ? isAllNewsLoading : isBookmarkedLoading;
  const isError = feedType === "all" ? isAllNewsError : isBookmarkedError;
  const isFetchingNextPage =
    feedType === "all" ? isAllNewsFetchingNextPage : isBookmarkedFetchingNextPage;
  const hasNextPage =
    feedType === "all" ? hasAllNewsNextPage : hasBookmarkedNextPage;
  const fetchNextPage =
    feedType === "all" ? fetchAllNewsNextPage : fetchBookmarkedNextPage;

  // Flatten all news items from all pages
  const allNewsItems = data ? data.pages.flatMap((page) => page.items) : [];

  // When in bookmarked view, ensure all items have is_bookmarked=true
  // This is needed because the backend doesn't explicitly set this flag
  // in the /bookmarks endpoint
  const newsItems = useMemo(() => {
    if (feedType === "bookmarked" && allNewsItems.length > 0) {
      return allNewsItems.map((item) => ({
        ...item,
        is_bookmarked: true,
      }));
    }
    return allNewsItems;
  }, [allNewsItems, feedType]);

  // Debounced function to update visible symbols
  const debouncedUpdateVisibleSymbols = useCallback(
    (visibleIndices: Set<number>) => {
      if (updateDebounceRef.current) {
        clearTimeout(updateDebounceRef.current);
      }

      updateDebounceRef.current = setTimeout(() => {
        // Get all unique coin symbols from visible news items
        const visibleSymbols = Array.from(visibleIndices)
          .filter((idx) => idx < newsItems.length) // Filter out loader row
          .flatMap((idx) => newsItems[idx].coins?.map((coin) => coin.symbol) || [])
          .filter((value, index, self) => self.indexOf(value) === index); // Unique symbols only

        // Only update if the symbols have actually changed
        if (!arraysHaveSameElements(visibleSymbols, lastSymbolsRef.current)) {
          console.log(`[NewsList] Visible symbols changed:`, visibleSymbols);

          // Unsubscribe from symbols no longer visible
          const symbolsToRemove = lastSymbolsRef.current.filter(
            (symbol) => !visibleSymbols.includes(symbol)
          );

          if (symbolsToRemove.length > 0) {
            console.log(
              `[NewsList] Removing subscriptions: ${symbolsToRemove.join(", ")}`
            );
            unsubscribeFromSymbols(symbolsToRemove);
          }

          // Subscribe to newly visible symbols
          const symbolsToAdd = visibleSymbols.filter(
            (symbol) => !lastSymbolsRef.current.includes(symbol)
          );

          if (symbolsToAdd.length > 0) {
            console.log(
              `[NewsList] Adding subscriptions: ${symbolsToAdd.join(", ")}`
            );
            subscribeToSymbols(symbolsToAdd);
          }

          lastSymbolsRef.current = visibleSymbols;
        }
      }, 200);
    },
    [newsItems, subscribeToSymbols, unsubscribeFromSymbols]
  );

  // Reset virtualizer when switching feed types
  const resetVirtualizerOnFeedChange = useCallback(() => {
    if (rowVirtualizer) {
      rowVirtualizer.scrollToIndex(0);
      visibleItemsRef.current = new Set();
      lastSymbolsRef.current = [];
    }
  }, []);

  // Set up virtualizer for rendering only visible items with dynamic measurement
  const rowVirtualizer = useVirtualizer({
    count: hasNextPage ? newsItems.length + 1 : newsItems.length, // +1 for loading row
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100, // Initial estimate, will be refined by actual measurements
    overscan: 5,
    measureElement: useCallback((element: Element | null) => {
      // Get actual height of the element including margins
      if (!element) return 100;
      const rect = element.getBoundingClientRect();
      return rect.height;
    }, []),
    // Update visible symbols when rendered items change
    onChange: (instance) => {
      const renderedIndices = new Set(
        instance.getVirtualItems().map((item) => item.index)
      );

      // Only process if visible items have changed
      if (!setsAreEqual(visibleItemsRef.current, renderedIndices)) {
        visibleItemsRef.current = renderedIndices;
        // Use debounced update to prevent frequent changes during scrolling
        debouncedUpdateVisibleSymbols(renderedIndices);
      }
    },
  });

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (updateDebounceRef.current) {
        clearTimeout(updateDebounceRef.current);
      }
    };
  }, []);

  // Update feed type and reset virtualizer
  const handleFeedTypeChange = (type: FeedType) => {
    setFeedType(type);
    resetVirtualizerOnFeedChange();
  };

  // Load more items when user scrolls to bottom
  useEffect(() => {
    const [lastItem] = [...rowVirtualizer.getVirtualItems()].reverse();

    if (!lastItem) {
      return;
    }

    if (
      lastItem.index >= newsItems.length - 1 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  }, [
    hasNextPage,
    fetchNextPage,
    newsItems.length,
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

  return (
    <>
      <div className="p-2 border-b border-border flex justify-between items-center">
        <h2 className="text-lg font-semibold">News Feed</h2>
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-1 px-3 py-1 text-sm rounded-md border border-input hover:bg-accent">
            {feedType === "all" ? "All News" : "Bookmarks"}
            <ChevronDown className="h-4 w-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={() => handleFeedTypeChange("all")}
              className={feedType === "all" ? "bg-accent" : ""}
            >
              All News
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => handleFeedTypeChange("bookmarked")}
              className={feedType === "bookmarked" ? "bg-accent" : ""}
            >
              Bookmarks
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {isError || isWebsocketError ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-destructive flex items-center justify-center gap-2">
            <AlertCircle className="size-6" />
            {isError ? "Connection has failed" : "Failed to load news"}
          </p>
        </div>
      ) : !isConnected || (isLoading && !newsItems.length) ? (
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
              const isLoaderRow = virtualRow.index > newsItems.length - 1;
              const item = newsItems[virtualRow.index];

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

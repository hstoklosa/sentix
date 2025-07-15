import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useSearch } from "@tanstack/react-router";
import { AlertCircle, ChevronDown, Layers, BookMarked } from "lucide-react";

import { Spinner } from "@/components/ui/spinner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { getBookmarkedPosts } from "@/features/bookmarks/api/get-bookmarks";

import { getPosts, useUpdatePostsCache, searchPosts } from "../api";
import { useLiveNews } from "../hooks";
import { NewsItem as NewsItemType } from "../types";
import { NewsItem, SearchBar, ContentFilter } from ".";

type FeedType = "all" | "bookmarked";

type DateFilter = {
  startDate?: Date;
  endDate?: Date;
  startTime?: string;
  endTime?: string;
  selectedCoins?: string[];
};

const NewsList = () => {
  const [feedType, setFeedType] = useState<FeedType>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFilter, setDateFilter] = useState<DateFilter>({});
  const [refreshCounter, setRefreshCounter] = useState(0);
  const parentRef = useRef<HTMLDivElement>(null);
  const loadingMoreRef = useRef(false);

  // Get the coin filter from the dashboard search params
  const search = useSearch({ from: "/_app/dashboard" });
  const coinFilter = search.coin !== "BTC" ? search.coin : undefined; // Don't filter for BTC (default)

  const {
    isConnected,
    error: isWebsocketError,
    registerMessageHandler,
    unregisterMessageHandler,
  } = useLiveNews();

  // Create cache update function with current query parameters
  const effectiveCoinFilter =
    dateFilter.selectedCoins && dateFilter.selectedCoins.length > 0
      ? dateFilter.selectedCoins[0] // Use first selected coin for now
      : coinFilter;

  const updatePostsCache = useUpdatePostsCache(dateFilter, effectiveCoinFilter);

  // Register the cache update function with the WebSocket context
  useEffect(() => {
    // Only register handler for main feed (all) without search query
    // Real-time updates should not affect bookmarked or search results
    if (feedType === "all" && !searchQuery) {
      console.log("Registering WebSocket handler for real-time news updates");
      registerMessageHandler((news: NewsItemType) => {
        console.log("Received real-time news:", news.title);
        updatePostsCache(news);
      });

      return () => {
        unregisterMessageHandler();
      };
    } else {
      // Unregister if not applicable
      console.log(
        "Unregistering WebSocket handler (not applicable for current view)"
      );
      unregisterMessageHandler();
    }
  }, [
    updatePostsCache,
    feedType,
    searchQuery,
    effectiveCoinFilter,
    registerMessageHandler,
    unregisterMessageHandler,
  ]);

  const { data, isLoading, isError, hasNextPage, fetchNextPage } = useInfiniteQuery(
    {
      queryKey: ["news-feed", feedType, searchQuery, dateFilter, coinFilter],
      queryFn: async ({ pageParam = 1 }) => {
        // Determine which coin filter to use
        // Priority: Content filter coins > URL-based coinFilter
        const effectiveCoinFilter =
          dateFilter.selectedCoins && dateFilter.selectedCoins.length > 0
            ? dateFilter.selectedCoins[0] // Use first selected coin for now
            : coinFilter;

        const params = {
          page: pageParam,
          page_size: 20,
          start_date: dateFilter.startDate?.toISOString(),
          end_date: dateFilter.endDate?.toISOString(),
          coin: effectiveCoinFilter,
        };

        if (searchQuery && feedType === "all") {
          return searchPosts(searchQuery, params);
        } else if (feedType === "all") {
          return getPosts(params);
        } else {
          // For bookmarked posts, pass the same filter parameters
          return getBookmarkedPosts({
            pageParam,
            query: searchQuery || undefined,
            start_date: dateFilter.startDate?.toISOString(),
            end_date: dateFilter.endDate?.toISOString(),
            coin: effectiveCoinFilter,
          });
        }
      },
      getNextPageParam: (lastPage) =>
        lastPage.has_next ? lastPage.page + 1 : undefined,
      initialPageParam: 1,
    }
  );

  const isSearchActive = !!searchQuery;
  const hasDateFilter = !!(dateFilter.startDate || dateFilter.endDate);
  const hasCoinFilter = !!(
    effectiveCoinFilter ||
    (dateFilter.selectedCoins && dateFilter.selectedCoins.length > 0)
  );

  const newsItems = useMemo(() => {
    const items = data ? data.pages.flatMap((page) => page.items) : [];
    if (feedType === "bookmarked" && !searchQuery) {
      return items.map((item) => ({ ...item, is_bookmarked: true }));
    }
    return items;
  }, [data, feedType, searchQuery]);

  const resetVirtualizerOnFeedChange = useCallback(() => {
    if (rowVirtualizer) {
      // Use a more stable way to scroll to top (do it after state updates)
      setTimeout(() => {
        if (parentRef.current) {
          parentRef.current.scrollTop = 0;
        }
      }, 0);
    }

    setSearchQuery("");
    setDateFilter({});
  }, []);

  // Set up virtualizer for rendering only visible items with dynamic measurement
  const rowVirtualizer = useVirtualizer({
    count: hasNextPage ? newsItems.length + 1 : newsItems.length, // +1 for loading row
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
    overscan: 5,
    getItemKey: (index) => {
      if (index === newsItems.length) return "loader";
      return newsItems[index]?.id || index;
    },
    measureElement: useCallback((element: Element | null) => {
      if (!element) return 100;
      const rect = element.getBoundingClientRect();
      return rect.height;
    }, []),
    scrollToFn: (offset, options, _) => {
      const scrollElement = parentRef.current;
      if (!scrollElement) return;

      if (options && options.behavior === "smooth") {
        scrollElement.scrollTo({
          top: offset,
          behavior: "smooth",
        });
      } else {
        scrollElement.scrollTop = offset;
      }
    },
    // onChange: (instance) => {},
  });

  const handleFeedTypeChange = (type: FeedType) => {
    setFeedType(type);
    resetVirtualizerOnFeedChange();
  };

  const handleSearch = (query: string) => {
    if (query === searchQuery) return;
    setSearchQuery(query);

    // Scroll to top after the state update and re-render
    setTimeout(() => {
      if (parentRef.current) {
        parentRef.current.scrollTop = 0;
      }
    }, 0);
  };

  const handleApplyDateFilters = (filters: DateFilter) => {
    setDateFilter(filters);

    // Scroll to top after applying filters
    setTimeout(() => {
      if (parentRef.current) {
        parentRef.current.scrollTop = 0;
      }
    }, 0);
  };

  const handleResetDateFilters = () => {
    setDateFilter({});

    // Scroll to top after resetting filters
    setTimeout(() => {
      if (parentRef.current) {
        parentRef.current.scrollTop = 0;
      }
    }, 0);
  };

  // Handle infinite scrolling more reliably with a separate
  // function that checks scroll position directly
  const checkAndLoadMore = useCallback(() => {
    if (loadingMoreRef.current || !hasNextPage || !parentRef.current) return;

    const container = parentRef.current;
    const { scrollTop, scrollHeight, clientHeight } = container;

    const scrollFraction = scrollTop / (scrollHeight - clientHeight);
    if (scrollFraction > 0.8) {
      loadingMoreRef.current = true;
      fetchNextPage().finally(() => {
        loadingMoreRef.current = false;
      });
    }
  }, [hasNextPage, fetchNextPage]);

  useEffect(() => {
    const scrollElement = parentRef.current;
    if (!scrollElement) return;

    const handleScroll = () => checkAndLoadMore();
    scrollElement.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      scrollElement.removeEventListener("scroll", handleScroll);
    };
  }, [checkAndLoadMore]);

  // Initial check for loading more data when component mounts or filters change
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      checkAndLoadMore();
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [checkAndLoadMore, feedType, searchQuery, dateFilter]);

  // Update refresh counter every 5 seconds to trigger relative time recalculation
  useEffect(() => {
    const interval = setInterval(() => {
      setRefreshCounter((count) => count + 1);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getLoadingMessage = () => {
    if (!isConnected) return "Connecting to news feed...";
    if (isSearchActive) return "Searching news...";
    if (coinFilter) return `Loading ${coinFilter} news...`;
    return isLoading ? "Loading news..." : "Waiting for news updates...";
  };

  const getEmptyStateMessage = () => {
    if (isSearchActive) return `No results found for "${searchQuery}"`;
    if (feedType === "bookmarked") return "No bookmarked items yet";
    if (hasDateFilter && hasCoinFilter) {
      const coinText =
        dateFilter.selectedCoins && dateFilter.selectedCoins.length > 0
          ? dateFilter.selectedCoins.join(", ")
          : effectiveCoinFilter;
      return `No news found for ${coinText} in the selected date range`;
    }
    if (hasDateFilter) return "No news items found for the selected date range";
    if (hasCoinFilter) {
      const coinText =
        dateFilter.selectedCoins && dateFilter.selectedCoins.length > 0
          ? dateFilter.selectedCoins.join(", ")
          : effectiveCoinFilter;
      return `No news found for ${coinText}`;
    }
    return "No news items available";
  };

  return (
    <>
      <div className="p-1.5 border-b border-border">
        {/* Coin filter indicator */}
        {(effectiveCoinFilter ||
          (dateFilter.selectedCoins && dateFilter.selectedCoins.length > 0)) && (
          <div className="mb-2 px-2 py-1 bg-primary/10 text-primary text-xs rounded-md border border-primary/20">
            Filtering by:{" "}
            {dateFilter.selectedCoins && dateFilter.selectedCoins.length > 0
              ? dateFilter.selectedCoins.join(", ")
              : effectiveCoinFilter}
          </div>
        )}

        <div className="flex items-center gap-2 h-8">
          <SearchBar
            onSearch={handleSearch}
            className="flex-1"
          />
          <ContentFilter
            startDate={dateFilter.startDate}
            endDate={dateFilter.endDate}
            startTime={dateFilter.startTime}
            endTime={dateFilter.endTime}
            selectedCoins={dateFilter.selectedCoins}
            onApplyFilters={handleApplyDateFilters}
            onResetFilters={handleResetDateFilters}
          />
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-1 px-1.5 py-1 h-7 text-sm rounded-md border border-input hover:bg-accent whitespace-nowrap">
              {feedType === "all" ? (
                <Layers className="size-3.5" />
              ) : (
                <BookMarked className="size-3.5" />
              )}
              <ChevronDown className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="[&>*:not(:last-child)]:mb-1"
            >
              <DropdownMenuItem
                onClick={() => handleFeedTypeChange("all")}
                className={feedType === "all" ? "bg-accent" : ""}
              >
                <Layers className="size-4" /> News
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => handleFeedTypeChange("bookmarked")}
                className={feedType === "bookmarked" ? "bg-accent" : ""}
              >
                <BookMarked className="size-4" /> Bookmarks
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
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
          <p className="text-muted-foreground">{getLoadingMessage()}</p>
        </div>
      ) : newsItems.length === 0 ? (
        <div className="flex items-center justify-center h-full py-10">
          <p className="text-muted-foreground">{getEmptyStateMessage()}</p>
        </div>
      ) : (
        <div
          ref={parentRef}
          className="flex-1 overflow-y-auto"
          style={{
            overflowAnchor: "none",
          }} /* Prevent browser from adjusting scroll position automatically */
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
                      <Spinner
                        size="sm"
                        className="min-h-[60px]"
                      />
                    ) : (
                      <div className="text-center py-4 text-muted-foreground">
                        No more news to load
                      </div>
                    )
                  ) : (
                    <NewsItem
                      news={item}
                      refreshCounter={refreshCounter}
                      // priceData={priceData}
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

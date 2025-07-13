import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { AlertCircle, ChevronDown, Layers, BookMarked } from "lucide-react";
import { useVirtualizer } from "@tanstack/react-virtual";

import { Spinner } from "@/components/ui/spinner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { NewsItem, SearchBar, ContentFilter } from ".";
import { getPosts, useUpdatePostsCache } from "../api/get-news";
import { searchPosts } from "../api/get-news"; // Assuming searchPosts is exported
import { getBookmarkedPosts } from "@/features/bookmarks/api/get-bookmarks";
import { useLiveNewsContext } from "../context";
import { useInfiniteQuery } from "@tanstack/react-query";

type FeedType = "all" | "bookmarked";

interface DateFilter {
  startDate?: Date;
  endDate?: Date;
  startTime?: string;
  endTime?: string;
}

const NewsList = () => {
  const [feedType, setFeedType] = useState<FeedType>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFilter, setDateFilter] = useState<DateFilter>({});
  const [refreshCounter, setRefreshCounter] = useState(0);
  const parentRef = useRef<HTMLDivElement>(null);
  const loadingMoreRef = useRef(false);
  const { isConnected, error: isWebsocketError } = useLiveNewsContext();

  const {
    data,
    isLoading,
    isError,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
  } = useInfiniteQuery({
    queryKey: ["news-feed", feedType, searchQuery, dateFilter],
    queryFn: async ({ pageParam = 1 }) => {
      const params = {
        page: pageParam,
        page_size: 20,
        start_date: dateFilter.startDate
          ? new Date(
              dateFilter.startDate.getFullYear(),
              dateFilter.startDate.getMonth(),
              dateFilter.startDate.getDate(),
              dateFilter.startTime
                ? parseInt(dateFilter.startTime.split(":")[0])
                : 0,
              dateFilter.startTime
                ? parseInt(dateFilter.startTime.split(":")[1])
                : 0,
              0
            ).toISOString()
          : undefined,
        end_date: dateFilter.endDate
          ? new Date(
              dateFilter.endDate.getFullYear(),
              dateFilter.endDate.getMonth(),
              dateFilter.endDate.getDate(),
              dateFilter.endTime ? parseInt(dateFilter.endTime.split(":")[0]) : 23,
              dateFilter.endTime ? parseInt(dateFilter.endTime.split(":")[1]) : 59,
              59
            ).toISOString()
          : undefined,
      };

      if (searchQuery) {
        return searchPosts(searchQuery, params);
      } else if (feedType === "all") {
        return getPosts(params);
      } else {
        return getBookmarkedPosts({ pageParam });
      }
    },
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
  });

  const updatePostsCache = useUpdatePostsCache(dateFilter);

  const isSearchActive = !!searchQuery;
  const hasDateFilter = !!(dateFilter.startDate || dateFilter.endDate);

  const newsItems = useMemo(() => {
    const items = data ? data.pages.flatMap((page) => page.items) : [];
    if (feedType === "bookmarked" && !searchQuery) {
      return items.map((item) => ({ ...item, is_bookmarked: true }));
    }
    return items;
  }, [data, feedType, searchQuery]);

  // Filter websocket updates based on active date filters
  const shouldIncludeWebsocketUpdate = useCallback(
    (newsItem: any) => {
      if (!hasDateFilter) return true;

      const itemDate = new Date(newsItem.time);
      const { startDate, endDate } = dateFilter;

      if (startDate && itemDate < startDate) return false;
      if (endDate && itemDate > endDate) return false;

      return true;
    },
    [dateFilter, hasDateFilter]
  );

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
    if (feedType === "bookmarked" && query) {
      setFeedType("all"); // Auto-switch to all for searching
    }
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
    return isLoading ? "Loading news..." : "Waiting for news updates...";
  };

  const getEmptyStateMessage = () => {
    if (isSearchActive) return `No results found for "${searchQuery}"`;
    if (feedType === "bookmarked") return "No bookmarked items yet";
    if (hasDateFilter) return "No news items found for the selected date range";
    return "No news items available";
  };

  return (
    <>
      <div className="p-1.5 border-b border-border">
        <div className="flex items-center gap-2 h-8">
          {feedType === "all" ? (
            <SearchBar
              onSearch={handleSearch}
              className="flex-1"
            />
          ) : (
            <p className="text-sm text-muted-foreground flex-1">
              Search is available in News view
            </p>
          )}
          <ContentFilter
            startDate={dateFilter.startDate}
            endDate={dateFilter.endDate}
            startTime={dateFilter.startTime}
            endTime={dateFilter.endTime}
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
                      <Spinner size="sm" />
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

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

import NewsItem from "./news-item";
import SearchBar from "./search-bar";
import {
  useGetInfinitePosts,
  useSearchInfinitePosts,
  useUpdatePostsCache,
} from "../api";
import { useGetInfiniteBookmarkedPosts } from "@/features/bookmarks/api/get-bookmarks";
import { useLiveNewsContext } from "../context";
// import usePriceData from "../hooks/use-price-data";

type FeedType = "all" | "bookmarked";

const NewsList = () => {
  const [feedType, setFeedType] = useState<FeedType>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [refreshCounter, setRefreshCounter] = useState(0);
  const parentRef = useRef<HTMLDivElement>(null);
  const loadingMoreRef = useRef(false);
  const { isConnected, error: isWebsocketError } = useLiveNewsContext();

  const {
    data: allNewsData,
    isLoading: isAllNewsLoading,
    isError: isAllNewsError,
    isFetchingNextPage: isAllNewsFetchingNextPage,
    hasNextPage: hasAllNewsNextPage,
    fetchNextPage: fetchAllNewsNextPage,
  } = useGetInfinitePosts();

  const {
    data: bookmarkedData,
    isLoading: isBookmarkedLoading,
    isError: isBookmarkedError,
    isFetchingNextPage: isBookmarkedFetchingNextPage,
    hasNextPage: hasBookmarkedNextPage,
    fetchNextPage: fetchBookmarkedNextPage,
  } = useGetInfiniteBookmarkedPosts();

  const {
    data: searchData,
    isLoading: isSearchLoading,
    isError: isSearchError,
    isFetchingNextPage: isSearchFetchingNextPage,
    hasNextPage: hasSearchNextPage,
    fetchNextPage: fetchSearchNextPage,
  } = useSearchInfinitePosts(searchQuery);

  const updatePostsCache = useUpdatePostsCache();

  const isSearchActive = !!searchQuery;

  const data = isSearchActive
    ? searchData
    : feedType === "all"
      ? allNewsData
      : bookmarkedData;

  const isLoading = isSearchActive
    ? isSearchLoading
    : feedType === "all"
      ? isAllNewsLoading
      : isBookmarkedLoading;

  const isError = isSearchActive
    ? isSearchError
    : feedType === "all"
      ? isAllNewsError
      : isBookmarkedError;

  const isFetchingNextPage = isSearchActive
    ? isSearchFetchingNextPage
    : feedType === "all"
      ? isAllNewsFetchingNextPage
      : isBookmarkedFetchingNextPage;

  const hasNextPage = isSearchActive
    ? hasSearchNextPage
    : feedType === "all"
      ? hasAllNewsNextPage
      : hasBookmarkedNextPage;

  const fetchNextPage = isSearchActive
    ? fetchSearchNextPage
    : feedType === "all"
      ? fetchAllNewsNextPage
      : fetchBookmarkedNextPage;

  const allNewsItems = data ? data.pages.flatMap((page) => page.items) : [];

  // When in bookmarked view, ensure all items have is_bookmarked=true
  const newsItems = useMemo(() => {
    if (feedType === "bookmarked" && !isSearchActive && allNewsItems.length > 0) {
      return allNewsItems.map((item) => ({
        ...item,
        is_bookmarked: true,
      }));
    }
    return allNewsItems;
  }, [allNewsItems, feedType, isSearchActive]);

  const resetVirtualizerOnFeedChange = useCallback(() => {
    if (rowVirtualizer) {
      // Use a more stable way to scroll to top - do it after state updates
      setTimeout(() => {
        if (parentRef.current) {
          parentRef.current.scrollTop = 0;
        }
      }, 0);
    }

    setSearchQuery("");
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

    // Reset tracking variables
    setSearchQuery(query);

    // Scroll to top after the state update and re-render
    setTimeout(() => {
      if (parentRef.current) {
        parentRef.current.scrollTop = 0;
      }
    }, 0);
  };

  // Handle infinite scrolling more reliably with a separate function
  // that checks scroll position directly
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
  }, [checkAndLoadMore, feedType, searchQuery]);

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
    return "No news items available";
  };

  return (
    <>
      <div className="p-1.5 border-b border-border">
        <div className="flex items-center gap-2 h-8">
          <SearchBar
            onSearch={handleSearch}
            className="flex-1"
          />
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-1 px-1.5 py-1 h-7 text-sm rounded-md border border-input hover:bg-accent whitespace-nowrap">
              {feedType === "all" ? (
                <Layers className="size-4" />
              ) : (
                <BookMarked className="size-4" />
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

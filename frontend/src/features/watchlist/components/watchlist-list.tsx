import { useRef, useCallback, useEffect } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { AlertCircle } from "lucide-react";

import { Spinner } from "@/components/ui/spinner";

import { useGetInfiniteCoins } from "../api/get-coins";
import WatchlistItem from "./watchlist-item";

const WatchlistList = () => {
  const parentRef = useRef<HTMLDivElement>(null);

  const {
    data,
    isLoading,
    isError,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
  } = useGetInfiniteCoins();
  const allCoins = data ? data.pages.flatMap((page) => page.items) : [];

  const rowVirtualizer = useVirtualizer({
    count: hasNextPage ? allCoins.length + 1 : allCoins.length, // +1 for loading row
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48, // estimated row height - reduced to account for smaller text
    overscan: 5,
    measureElement: useCallback((element: Element | null) => {
      // Get actual height of the element including margins
      if (!element) return 48;
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
      lastItem.index >= allCoins.length - 1 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  }, [
    hasNextPage,
    fetchNextPage,
    allCoins.length,
    isFetchingNextPage,
    rowVirtualizer.getVirtualItems(),
  ]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* bg-muted/30 */}
      <div className="flex items-center h-[45px] px-2.5 py-2 border-b border-border">
        <h2 className="text-md font-semibold">Watchlist</h2>
      </div>

      {isError ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-destructive flex items-center justify-center gap-2">
            <AlertCircle className="size-6" />
            Failed to load coins
          </p>
        </div>
      ) : isLoading && !allCoins.length ? (
        <div className="flex flex-row items-center justify-center h-full py-6 gap-3">
          <Spinner size="md" />
          <p className="text-muted-foreground">Loading coins...</p>
        </div>
      ) : (
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* bg-background */}
          <div className="px-3 py-2 text-[10px] text-muted-foreground border-b border-border sticky top-0 z-10">
            <div className="flex items-center">
              <div className="w-[58.5%]">ASSET</div>
              <div className="w-[16%]">PRICE</div>
              <div className="w-[14.5%]">CHANGE %</div>
              <div className="w-[10%]">MCAP</div>
            </div>
          </div>

          <div
            ref={parentRef}
            className="flex-1 overflow-y-auto"
            style={{ minHeight: 0 }}
          >
            <div
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`,
                width: "100%",
                position: "relative",
              }}
            >
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const isLoaderRow = virtualRow.index > allCoins.length - 1;
                const coin = allCoins[virtualRow.index];

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
                        <div className="flex justify-center items-center py-3">
                          <Spinner size="sm" />
                          <span className="ml-2 text-xs text-muted-foreground">
                            Loading more coins...
                          </span>
                        </div>
                      ) : (
                        <div className="text-center py-3 text-xs text-muted-foreground">
                          No more coins to load
                        </div>
                      )
                    ) : (
                      <WatchlistItem coin={coin} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WatchlistList;

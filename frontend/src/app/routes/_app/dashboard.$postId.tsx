import { useEffect, useRef, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { toast } from "sonner";
import {
  Info,
  ExternalLink,
  X,
  Copy,
  Link as LinkIcon,
  Bookmark,
  ChevronsUpDown,
  Coins,
} from "lucide-react";

import xIcon from "@/assets/x.png";
import newsIcon from "@/assets/news.png";

import { Spinner } from "@/components/ui/spinner";
import { formatDateTime } from "@/utils/format";
import { cn } from "@/lib/utils";

import { useGetPost } from "@/features/news/api";
import CoinTag from "@/features/news/components/coin-tag";
import useCoinSubscription from "@/features/coins/hooks/use-coin-subscription";
import { useCreateBookmark } from "@/features/bookmarks/api/create-bookmark";
import { useDeleteBookmark } from "@/features/bookmarks/api/delete-bookmark";
import { PriceChart } from "@/features/market/components";
import { DashboardPanel } from "../_app/dashboard";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function PostComponent() {
  const { postId } = Route.useParams() as { postId: string };
  const previousSymbolsRef = useRef<string[]>([]);
  const { data: post, isLoading, error } = useGetPost(parseInt(postId, 10));
  const { subscribeToSymbols, unsubscribeFromSymbols } = useCoinSubscription();
  const [selectedCoinId, setSelectedCoinId] = useState<string>("bitcoin");
  const selectedCoin = post?.coins.find(
    (coin) =>
      (coin.name?.toLowerCase() || coin.symbol.toLowerCase()) === selectedCoinId
  );

  const createBookmark = useCreateBookmark({
    onSuccess: () => toast.success("The post has been added to bookmarks"),
    onError: () => toast.error("Failed to bookmark this post"),
  });
  const deleteBookmark = useDeleteBookmark({
    onSuccess: () => toast.success("The post has been removed from bookmarks"),
    onError: () => toast.error("Failed to remove this post from bookmarks"),
  });

  // Subscribe to all coin prices in this post where cleanup
  // is handled automatically by useCoinSubscription hook.
  useEffect(() => {
    if (!post?.coins?.length) return;

    const symbols = post.coins.map((coin) => coin.symbol);
    const symbolsChanged =
      previousSymbolsRef.current.length !== symbols.length ||
      symbols.some((symbol) => !previousSymbolsRef.current.includes(symbol));

    if (symbolsChanged) {
      console.log(
        `[PostDetail] Updating coin subscriptions: ${symbols.join(", ")}`
      );

      // Unsubscribe from symbols that are no longer needed
      const symbolsToRemove = previousSymbolsRef.current.filter(
        (prevSymbol) => !symbols.includes(prevSymbol)
      );

      if (symbolsToRemove.length > 0) {
        console.log(
          `[PostDetail] Removing subscriptions: ${symbolsToRemove.join(", ")}`
        );
        unsubscribeFromSymbols(symbolsToRemove);
      }

      // Subscribe to new symbols
      const symbolsToAdd = symbols.filter(
        (symbol) => !previousSymbolsRef.current.includes(symbol)
      );

      if (symbolsToAdd.length > 0) {
        console.log(
          `[PostDetail] Adding subscriptions: ${symbolsToAdd.join(", ")}`
        );
        subscribeToSymbols(symbolsToAdd);
      }

      previousSymbolsRef.current = [...symbols];
    }
  }, [post, subscribeToSymbols, unsubscribeFromSymbols]);

  // Set the default selected coin when post loads or changes
  useEffect(() => {
    if (post?.coins?.length) {
      setSelectedCoinId(
        post.coins[0].name?.toLowerCase() || post.coins[0].symbol.toLowerCase()
      );
    } else {
      setSelectedCoinId("bitcoin");
    }
  }, [post]);

  if (isLoading) {
    return (
      <Spinner
        className="h-full w-full"
        size="md"
      />
    );
  }

  if (error || !post) {
    return (
      <div className="flex h-full items-center justify-center gap-3">
        <Info className="size-8 text-muted-foreground" />
        <h2 className="text-lg text-muted-foreground font-normal">
          An error occurred while loading the post
        </h2>
      </div>
    );
  }

  const handleBookmarkToggle = () => {
    if (!post) return;

    post.is_bookmarked
      ? deleteBookmark.mutate(post.id)
      : createBookmark.mutate({ news_item_id: post.id });
  };

  const handleCopyTitle = () => {
    navigator.clipboard
      .writeText(post.title)
      .then(() => toast.success("The title has been copied to clipboard"))
      .catch(() => toast.error("Failed to copy title to clipboard"));
  };

  const handleCopyUrl = () => {
    navigator.clipboard
      .writeText(post.url)
      .then(() => toast.success("The URL has been copied to clipboard"))
      .catch(() => toast.error("Failed to copy URL to clipboard"));
  };

  const handleCoinChange = (coinId: string) => {
    setSelectedCoinId(coinId);
  };

  // Use selectedCoinId directly without fallback
  const chartCoinId = selectedCoinId;

  return (
    <div className="grid grid-rows-2 h-full w-full gap-2">
      {/* Top section - Post content */}
      <DashboardPanel position={{ rowStart: 1, colStart: 1 }}>
        <div className="flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-2 px-2.5 py-2 border-b border-border">
            <div
              className={cn(
                "flex justify-center items-center min-w-8 min-h-8 rounded-full bg-primary/10",
                post.source === "Twitter" ? "bg-black" : "bg-[#7233F7]"
              )}
            >
              <img
                src={post.source === "Twitter" ? xIcon : newsIcon}
                alt="X"
                className="size-4"
              />
            </div>
            <div className="flex flex-col text-xs">
              <div className="flex items-center gap-1">
                <span className="text-sm text-foreground capitalize">
                  {post.source}
                </span>
                <a
                  aria-label="Read more"
                  href={post.url}
                  target="_blank"
                  className="flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="size-3.5" />
                </a>
              </div>
              <span className="text-muted-foreground">
                {formatDateTime(post.time)}
              </span>
            </div>

            <div className="ml-auto flex items-center gap-3">
              <button
                aria-label={post.is_bookmarked ? "Remove bookmark" : "Add bookmark"}
                title={post.is_bookmarked ? "Remove bookmark" : "Add bookmark"}
                className={cn(
                  "flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors",
                  post.is_bookmarked && "text-primary"
                )}
                onClick={handleBookmarkToggle}
              >
                <Bookmark
                  className="size-3.5"
                  fill={post.is_bookmarked ? "currentColor" : "none"}
                />
              </button>
              <button
                aria-label="Copy Title"
                className="flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors"
                onClick={handleCopyTitle}
              >
                <Copy className="size-3.5" />
              </button>
              <button
                aria-label="Copy URL"
                className="flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors"
                onClick={handleCopyUrl}
              >
                <LinkIcon className="size-3.5" />
              </button>

              <Link
                to="/dashboard"
                className="flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors ml-[-4px]"
              >
                <X className="size-4.5" />
              </Link>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-muted-foreground/20 scrollbar-track-transparent">
            <div className="flex flex-col gap-2 p-2.5">
              <h2 className="text-xl font-bold">{post.title}</h2>
              {/* {post.image_url && (
                <img
                  src={post.image_url}
                  alt={post.title}
                  className="rounded-lg w-full max-h-80 object-cover"
                />
              )} */}

              <div className="prose prose-sm dark:prose-invert line-break">
                {post.body ? post.body : post.title}
              </div>

              {post.coins.length > 0 && (
                <div className="mt-2">
                  <h3 className="text-sm font-medium mb-2">Related Coins:</h3>
                  <div className="flex flex-wrap gap-2">
                    {post.coins.map((coin) => (
                      <CoinTag
                        key={coin.id}
                        symbol={coin.symbol}
                        priceUsd={coin.price_usd}
                        priceTimestamp={coin.price_timestamp}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </DashboardPanel>

      {/* Bottom section - Price chart */}
      <DashboardPanel position={{ rowStart: 2, colStart: 1 }}>
        <div className="flex flex-col h-full">
          {post.coins.length > 0 && chartCoinId ? (
            <PriceChart
              coinId={chartCoinId}
              headerLeft={
                <Select
                  value={selectedCoinId}
                  onValueChange={handleCoinChange}
                >
                  <SelectTrigger className="h-7 w-auto min-w-auto">
                    <SelectValue placeholder="Select coin">
                      {selectedCoin && (
                        <div className="flex items-center">
                          {selectedCoin.image_url ? (
                            <img
                              src={selectedCoin.image_url}
                              alt={selectedCoin.symbol}
                              className="w-4 h-4 mr-2 rounded-full"
                            />
                          ) : (
                            <Coins className="w-4 h-4 mr-2 text-muted-foreground" />
                          )}
                          <span className="font-medium">{selectedCoin.symbol}</span>
                        </div>
                      )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {post.coins.map((coin) => (
                      <SelectItem
                        key={coin.id}
                        value={
                          coin.name?.toLowerCase() || coin.symbol.toLowerCase()
                        }
                      >
                        <div className="flex items-center">
                          {coin.image_url ? (
                            <img
                              src={coin.image_url}
                              alt={coin.symbol}
                              className="w-5 h-5 mr-2 rounded-full"
                            />
                          ) : (
                            <Coins className="w-5 h-5 mr-2 text-muted-foreground" />
                          )}
                          <span className="font-medium">{coin.symbol}</span>
                          <span className="text-xs text-muted-foreground ml-2">
                            {coin.name || coin.symbol}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              }
            />
          ) : (
            <div className="flex h-full items-center justify-center flex-col gap-2 p-4">
              <Info className="size-8 text-muted-foreground" />
              <div className="flex flex-col items-center justify-center gap-1">
                <h3 className="text-lg text-muted-foreground font-normal">
                  No coin data available for this post
                </h3>
                <p className="text-sm text-muted-foreground/70">
                  This post isn't associated with any specific cryptocurrency
                </p>
              </div>
            </div>
          )}
        </div>
      </DashboardPanel>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard/$postId")({
  component: PostComponent,
});

import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Info,
  ExternalLink,
  X,
  Copy,
  Link as LinkIcon,
  Bookmark,
} from "lucide-react";
import { useEffect, useRef } from "react";

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

function PostComponent() {
  const { postId } = Route.useParams() as { postId: string };
  const { data: post, isLoading, error } = useGetPost(parseInt(postId, 10));
  const previousSymbolsRef = useRef<string[]>([]);
  const { subscribeToSymbols, unsubscribeFromSymbols } = useCoinSubscription();
  const createBookmark = useCreateBookmark();
  const deleteBookmark = useDeleteBookmark();

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

  const handleBookmarkToggle = () => {
    if (!post) return;

    post.is_bookmarked
      ? deleteBookmark.mutate(post.id)
      : createBookmark.mutate({ news_item_id: post.id });
  };

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

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text).catch((error) => {
      console.error(`Failed to copy: ${error}`);
    });
  };

  return (
    <div className="flex flex-col h-full">
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
          <span className="text-muted-foreground">{formatDateTime(post.time)}</span>
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
            onClick={(_) => handleCopy(post.title)}
          >
            <Copy className="size-3.5" />
          </button>
          <button
            aria-label="Copy URL"
            className="flex items-center justify-center rounded-sm text-muted-foreground hover:text-primary transition-colors"
            onClick={(_) => handleCopy(post.url)}
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
          {post.image_url && (
            <img
              src={post.image_url}
              alt={post.title}
              className="rounded-lg w-full max-h-80 object-cover"
            />
          )}

          <div className="prose prose-sm dark:prose-invert line-break-anywhere">
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
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard/$postId")({
  component: PostComponent,
});

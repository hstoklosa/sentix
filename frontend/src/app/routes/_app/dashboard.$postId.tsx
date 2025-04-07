import { createFileRoute } from "@tanstack/react-router";
import { Info, ExternalLink } from "lucide-react";

import xIcon from "@/assets/x.png";
import newsIcon from "@/assets/news.png";

import { Spinner } from "@/components/ui/spinner";
import { formatDateTime } from "@/utils/format";

import { useGetPost } from "@/features/news/api";
import { cn } from "@/lib/utils";

function PostComponent() {
  const { postId } = Route.useParams() as { postId: string };
  const { data: post, isLoading, error } = useGetPost(parseInt(postId, 10));

  if (isLoading) {
    return (
      <Spinner
        fullScreen
        size="lg"
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

  return (
    <div className="flex flex-col">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 p-2.5 border-b border-border">
          <div
            className={cn(
              "flex justify-center items-center min-w-8 min-h-8 rounded-full bg-primary/10",
              post.source === "Twitter" ? "bg-black" : "bg-[#7233F7]"
            )}
          >
            {post.source === "Twitter" ? (
              <img
                src={xIcon}
                alt="X"
                className="size-4"
              />
            ) : (
              <img
                src={newsIcon}
                alt="News"
                className="w-4"
              />
            )}
          </div>
          <div className="flex flex-col text-xs">
            <span className="text-foreground capitalize">{post.source}</span>
            <span className="text-muted-foreground">
              {formatDateTime(post.time)}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-2 p-2.5">
        <h2 className="text-xl font-bold">{post.title}</h2>
        {post.image_url && (
          <img
            src={post.image_url}
            alt={post.title}
            className="rounded-lg w-full max-h-80 object-cover"
          />
        )}

        <div className="prose prose-sm dark:prose-invert">
          {post.body ? <>{post.body}</> : <>{post.title}</>}
        </div>

        {post.coins.length > 0 && (
          <div className="mt-2">
            <h3 className="text-sm font-medium mb-2">Related Coins:</h3>
            <div className="flex flex-wrap gap-2">
              {post.coins.map((coin) => (
                <span
                  key={coin.id}
                  className="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs"
                >
                  {coin.name || coin.symbol}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard/$postId")({
  component: PostComponent,
});

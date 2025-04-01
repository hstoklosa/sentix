import { createFileRoute, useRouter } from "@tanstack/react-router";
import { useEffect, useState, useRef } from "react";

import { Button } from "@/components/ui/button";

import { useLogout } from "@/features/auth/api/logout";
import { useNewsWebSocket } from "@/features/news/hooks";
import { NewsItem } from "@/features/news/types";

function RouteComponent() {
  const router = useRouter();
  const navigate = Route.useNavigate();
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);

  // const logoutMutation = useLogout({
  //   onSuccess: () => {
  //     router.invalidate().finally(() => {
  //       navigate({ to: "/" });
  //     });
  //   },
  // });

  const handleNewsMessage = (news: NewsItem) => {
    setNewsItems((prev) => [news, ...prev].slice(0, 100)); // Keep last 100 items
  };

  // Use the WebSocket hook - auto-connects on mount
  const { isConnected, error } = useNewsWebSocket({
    onMessage: handleNewsMessage,
  });

  return (
    <>
      {/* <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className="text-sm">
            WebSocket:{" "}
            {isConnected ? (
              <span className="text-chart-1">Connected</span>
            ) : (
              <span className="text-destructive">Disconnected</span>
            )}
          </div>
          <Button onClick={() => logoutMutation.mutate(undefined)}>Logout</Button>
        </div>
      </div> */}

      <div className="grid grid-cols-[repeat(3,1fr)] grid-rows-[repeat(3,1fr)] gap-x-2 gap-y-2 h-[calc(100vh-2rem)] overflow-hidden">
        <div className="row-start-1 row-end-4 col-start-1 col-end-2 flex flex-col border-1 border-border rounded-md">
          <div className="p-4 rounded-lg shadow mb-2">
            <h2 className="text-xl font-semibold mb-4">News Feed</h2>
            <p className="text-sm text-muted-foreground">
              Live cryptocurrency news and updates.
            </p>
            {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
          </div>

          <div className="p-4 rounded-lg shadow flex-1 overflow-y-auto">
            {newsItems.length === 0 ? (
              <p className="text-muted-foreground">Waiting for news updates...</p>
            ) : (
              <div className="space-y-4">
                {newsItems.map((item, index) => (
                  <div
                    key={index}
                    className="border-b border-border pb-4"
                  >
                    <h3 className="font-medium">{item.title}</h3>
                    <p className="text-sm text-muted-foreground">{item.body}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="row-start-1 row-end-2 col-start-2 col-end-4 flex flex-col border-1 border-border rounded-md">
          2
        </div>

        <div className="row-start-2 row-end-4 col-start-2 col-end-3 flex flex-col border-1 border-border rounded-md">
          3
        </div>

        <div className="row-start-2 row-end-4 col-start-3 col-end-4 flex flex-col border-1 border-border rounded-md">
          4
        </div>
      </div>
    </>
  );
}

export const Route = createFileRoute("/_app/dashboard")({
  component: RouteComponent,
  head: () => ({
    meta: [{ title: "Dashboard | Sentix" }],
  }),
});

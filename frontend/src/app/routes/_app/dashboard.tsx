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

  const logoutMutation = useLogout({
    onSuccess: () => {
      router.invalidate().finally(() => {
        navigate({ to: "/" });
      });
    },
  });

  const handleNewsMessage = (news: NewsItem) => {
    setNewsItems((prev) => [news, ...prev].slice(0, 100)); // Keep last 100 items
  };

  // Use the WebSocket hook - auto-connects on mount
  const { isConnected, error } = useNewsWebSocket({
    onMessage: handleNewsMessage,
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className="text-sm">
            WebSocket:{" "}
            {isConnected ? (
              <span className="text-green-500">Connected</span>
            ) : (
              <span className="text-red-500">Disconnected</span>
            )}
          </div>
          <Button onClick={() => logoutMutation.mutate(undefined)}>Logout</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Sidebar */}
        <div className="col-span-1 md:col-span-3">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">News Feed</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Live cryptocurrency news and updates.
            </p>
            {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
          </div>
        </div>

        {/* News list */}
        <div className="col-span-1 md:col-span-9">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            {newsItems.length === 0 ? (
              <p className="text-gray-500">Waiting for news updates...</p>
            ) : (
              <div className="space-y-4">
                {newsItems.map((item, index) => (
                  <div
                    key={index}
                    className="border-b pb-4"
                  >
                    <h3 className="font-medium">{item.title}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {item.body}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard")({
  component: RouteComponent,
  head: () => ({
    meta: [{ title: "Dashboard | Sentix" }],
  }),
});

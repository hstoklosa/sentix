import React, { useEffect } from "react";

import useAuth from "@/hooks/use-auth";
import { Spinner } from "@/components/ui";

import { NewsItem } from "./news-item";
import { useNewsState } from "../api";

type NewsListProps = {
  maxItems?: number;
};

export const NewsList: React.FC<NewsListProps> = ({ maxItems = 20 }) => {
  const auth = useAuth();
  const isAuthenticated = auth.status === "AUTHENTICATED";
  const isPending = auth.status === "PENDING";

  const authToken = localStorage.getItem("access_token");
  const token = authToken ? JSON.parse(authToken) : null;

  const {
    newsItems,
    isLoading,
    error,
    isConnected,
    connect,
    refreshConnection,
    recentNewsIds,
  } = useNewsState({
    autoConnect: isAuthenticated,
    maxItems,
    authToken: token,
  });

  // Reconnect when authentication state changes
  useEffect(() => {
    if (isAuthenticated) {
      connect();
    }
  }, [isAuthenticated, connect]);

  // Refresh connection when token might be expired
  useEffect(() => {
    const interval = setInterval(
      () => {
        if (isAuthenticated && isConnected) {
          refreshConnection();
        }
      },
      50 * 60 * 1000
    );

    return () => clearInterval(interval);
  }, [isAuthenticated, isConnected, refreshConnection]);

  // Render loading state when auth state is pending
  if (isPending) {
    return (
      <div className="min-h-[200px] flex items-center justify-center">
        <Spinner
          size="md"
          variant="primary"
        />
        <span className="ml-2 text-gray-600">Checking authentication...</span>
      </div>
    );
  }

  // Render login prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="news-list">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-800">Latest News</h2>
        </div>
        <div className="p-6 bg-blue-50 text-blue-700 rounded-lg text-center">
          <h3 className="font-semibold mb-2">Authentication Required</h3>
          <p>Please log in to access real-time news updates.</p>
        </div>
      </div>
    );
  }

  // Render loading state for news data
  if (isLoading) {
    return (
      <div className="min-h-[200px] flex items-center justify-center">
        <Spinner
          size="md"
          variant="primary"
        />
        <span className="ml-2 text-gray-600">Loading news...</span>
      </div>
    );
  }

  return (
    <div className="news-list">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Latest News</h2>
        <div className="flex items-center text-sm">
          <span
            className={`inline-block w-2 h-2 rounded-full mr-2 ${
              isConnected ? "bg-green-500" : "bg-red-500"
            }`}
          ></span>
          <span className="text-gray-600">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
          {!isConnected && isAuthenticated && (
            <button
              onClick={() => connect()}
              className="ml-2 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 py-1 px-2 rounded"
            >
              Reconnect
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 mb-4 bg-yellow-50 text-yellow-700 text-sm rounded">
          <div className="font-semibold">WebSocket error:</div>
          <div>{error}</div>
          <button
            onClick={() => connect()}
            className="mt-2 text-xs bg-yellow-100 hover:bg-yellow-200 text-yellow-700 py-1 px-2 rounded"
          >
            Try Reconnecting
          </button>
        </div>
      )}

      {newsItems.length === 0 ? (
        <div className="text-center p-8 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No news items available at the moment.</p>
        </div>
      ) : (
        <div>
          {newsItems.slice(0, maxItems).map((item, index) => {
            const newsId = `${item.title}-${item.time}`
              .replace(/\s+/g, "-")
              .toLowerCase();
            return (
              <NewsItem
                key={`${newsId}-${index}`}
                news={item}
                isHighlighted={recentNewsIds[newsId]}
              />
            );
          })}

          {newsItems.length > maxItems && (
            <div className="text-center mt-4">
              <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors">
                Load More
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

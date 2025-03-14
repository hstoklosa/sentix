import { useState, useCallback, useEffect } from "react";

import { NewsItem } from "../types";
import { useNewsWebSocket } from "./use-news-websocket";

type UseNewsStateOptions = {
  autoConnect?: boolean;
  maxItems?: number;
  authToken?: string;
};

type UseNewsStateResult = {
  newsItems: NewsItem[];
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  refreshConnection: () => Promise<void>;
  recentNewsIds: Record<string, boolean>;
};

/**
 * Hook to manage news state using WebSocket connection
 *
 * This hook maintains a list of news items received from the WebSocket
 * and provides functions to control the WebSocket connection.
 *
 * @param options Configuration options
 * @returns News state and WebSocket control functions
 */
export const useNewsState = ({
  autoConnect = false,
  maxItems = 100,
  authToken,
}: UseNewsStateOptions = {}): UseNewsStateResult => {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [recentNewsIds, setRecentNewsIds] = useState<Record<string, boolean>>({});

  // Function to generate a unique ID for a news item
  const getNewsId = useCallback((item: NewsItem) => {
    return `${item.title}-${item.time}`.replace(/\s+/g, "-").toLowerCase();
  }, []);

  const handleNewMessage = useCallback(
    (newItem: NewsItem) => {
      const newsId = getNewsId(newItem);

      setNewsItems((prevItems) => {
        // Check if this item already exists (by ID)
        const exists = prevItems.some((item) => getNewsId(item) === newsId);

        if (exists) {
          return prevItems; // Don't add duplicates
        }

        // Add new item at the beginning and limit the total number
        return [newItem, ...prevItems].slice(0, maxItems);
      });

      // Mark this item as recently received (for highlighting)
      setRecentNewsIds((prev) => ({ ...prev, [newsId]: true }));

      // After 3 seconds, remove the highlight
      setTimeout(() => {
        setRecentNewsIds((prev) => {
          const updated = { ...prev };
          delete updated[newsId];
          return updated;
        });
      }, 3000);

      // News has been loaded
      setIsLoading(false);
    },
    [getNewsId, maxItems]
  );

  const {
    isConnected,
    error,
    connect: wsConnect,
    disconnect,
    refreshConnection,
  } = useNewsWebSocket({
    onMessage: handleNewMessage,
    autoConnect,
    authToken,
  });

  // Custom connect function that sets loading state
  const connect = useCallback(async () => {
    setIsLoading(true);
    await wsConnect();
  }, [wsConnect]);

  // Set loading to false after a timeout if no news is received
  useEffect(() => {
    let timeoutId: number | null = null;

    if (isLoading && isConnected) {
      timeoutId = window.setTimeout(() => {
        setIsLoading(false);
      }, 5000); // wait 5 seconds for initial data
    }

    return () => {
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [isLoading, isConnected]);

  return {
    newsItems,
    isLoading,
    error,
    isConnected,
    connect,
    disconnect,
    refreshConnection,
    recentNewsIds,
  };
};

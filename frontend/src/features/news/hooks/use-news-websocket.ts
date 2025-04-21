import { useState, useEffect, useRef } from "react";

import { NewsItem } from "../types";

type UseNewsWebSocketOptions = {
  onMessage?: (news: NewsItem) => void;
  autoConnect?: boolean;
  authToken?: string;
  baseUrl?: string;
  defaultProvider?: string;
};

type UseNewsWebSocketResult = {
  isConnected: boolean;
  error: string | null;
  currentProvider: string | null;
  availableProviders: string[];
  connect: () => void;
  disconnect: () => void;
  subscribe: (provider: string) => void;
  unsubscribe: () => void;
  refreshProviders: () => void;
};

/**
 * WebSocket hook for connecting to the news WebSocket API with provider subscription support
 */
export const useNewsWebSocket = ({
  onMessage,
  autoConnect = true,
  authToken,
  baseUrl = "ws://localhost:8000",
  defaultProvider = "CoinDesk",
}: UseNewsWebSocketOptions = {}): UseNewsWebSocketResult => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentProvider, setCurrentProvider] = useState<string | null>(null);
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const isInitialConnectionRef = useRef(true);

  // Clean up function
  const disconnect = () => {
    if (pingIntervalRef.current) {
      window.clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;

      try {
        wsRef.current.close();
      } catch (err) {}

      wsRef.current = null;
    }

    setIsConnected(false);
    setCurrentProvider(null);
  };

  // Helper to send a message to the WebSocket
  const sendMessage = (data: any): boolean => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return false;
    }

    try {
      wsRef.current.send(JSON.stringify(data));
      return true;
    } catch (error) {
      console.error("Error sending WebSocket message:", error);
      return false;
    }
  };

  // Get available providers
  const refreshProviders = () => {
    if (isConnected) {
      sendMessage({ type: "get_available_feeds" });
    }
  };

  // Subscribe to a specific provider
  const subscribe = (provider: string) => {
    if (isConnected && provider) {
      sendMessage({
        type: "subscribe",
        feed: provider,
      });
    }
  };

  // Unsubscribe from current provider
  const unsubscribe = () => {
    if (isConnected) {
      sendMessage({ type: "unsubscribe" });
    }
  };

  const connect = () => {
    // Don't reconnect if already connected
    if (wsRef.current) return;
    disconnect();
    setError(null);

    try {
      const rawToken = authToken || localStorage.getItem("access_token") || "";
      const token = rawToken.replace(/^["'](.*)["']$/, "$1");

      if (!token) {
        setError("Not authenticated");
        return;
      }

      const clientId = Math.floor(Math.random() * 1000000).toString();
      const wsUrl = `${baseUrl}/api/v1/news/ws/${clientId}?token=${token}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("Connected to WebSocket:", wsUrl);
        setIsConnected(true);
        setError(null);

        // Setup ping interval
        pingIntervalRef.current = window.setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 30000);

        // Get available providers
        sendMessage({ type: "get_available_feeds" });

        // Get current subscription
        sendMessage({ type: "get_subscription" });

        // After a short delay, explicitly subscribe to the default provider
        // This ensures we always make the subscription request
        setTimeout(() => {
          console.log(
            `Explicitly subscribing to default provider: ${defaultProvider}`
          );
          sendMessage({
            type: "subscribe",
            feed: defaultProvider,
          });
          isInitialConnectionRef.current = false;
        }, 500);
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${event.code}`);
        setIsConnected(false);
        setCurrentProvider(null);

        if (pingIntervalRef.current) {
          window.clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
      };

      ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        setError("WebSocket error occurred");
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          // Handle different message types
          switch (message.type) {
            case "news":
              if (message.data && onMessage) {
                onMessage(message.data);
              }
              break;

            case "pong":
              console.debug("Received pong from server");
              break;

            case "available_feeds":
              if (Array.isArray(message.feeds)) {
                setAvailableProviders(message.feeds);

                // Check if we need to subscribe - no condition on currentProvider
                // since it might not be updated yet due to React state batching
                if (
                  isInitialConnectionRef.current &&
                  message.feeds.includes(defaultProvider)
                ) {
                  subscribe(defaultProvider);
                  isInitialConnectionRef.current = false;
                }
              }
              break;

            case "subscription":
              setCurrentProvider(message.feed);

              // If we receive a null subscription, check if we need to subscribe
              if (message.feed === null && isInitialConnectionRef.current) {
                // Don't check availableProviders here as it might not be updated yet
                // We'll handle subscription in the available_feeds case
                console.log(
                  "No current subscription, will wait for available_feeds"
                );
              }
              break;

            case "subscribed":
              setCurrentProvider(message.feed);
              break;

            case "unsubscribed":
              setCurrentProvider(null);
              break;

            case "error":
              setError(message.message || "An error occurred");
              break;
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      setError(error instanceof Error ? error.message : "Failed to connect");
    }
  };

  // Connect on mount if autoConnect is true
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => disconnect();
  }, [autoConnect]); // Only depend on autoConnect

  return {
    isConnected,
    error,
    currentProvider,
    availableProviders,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    refreshProviders,
  };
};

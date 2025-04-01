import { useState, useEffect, useRef } from "react";

import { NewsItem } from "../types";

type UseNewsWebSocketOptions = {
  onMessage?: (news: NewsItem) => void;
  autoConnect?: boolean;
  authToken?: string;
  baseUrl?: string;
};

type UseNewsWebSocketResult = {
  isConnected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
};

/**
 * Simple WebSocket hook for connecting to the news WebSocket API
 */
export const useNewsWebSocket = ({
  onMessage,
  autoConnect = true,
  authToken,
  baseUrl = "ws://localhost:8000",
}: UseNewsWebSocketOptions = {}): UseNewsWebSocketResult => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<number | null>(null);

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

        pingIntervalRef.current = window.setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 30000);
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${event.code}`);
        setIsConnected(false);

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

          if (message.type === "news" && message.data && onMessage) {
            onMessage(message.data);
          } else if (message.type === "pong") {
            console.debug("Received pong from server");
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
    if (autoConnect) connect();
    return () => disconnect();
  }, []);

  return {
    isConnected,
    error,
    connect,
    disconnect,
  };
};

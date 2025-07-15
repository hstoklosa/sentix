import { useState, useEffect, useRef, useCallback } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";

import { useLocalStorage } from "@/hooks/use-local-storage";

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
  connect: () => void;
  disconnect: () => void;
};

/**
 * WebSocket hook for connecting to the news WebSocket API with provider subscription support
 */
export const useNewsWebSocket = ({
  baseUrl = "ws://localhost:8000",
  authToken,
  onMessage,
  defaultProvider = "TreeNews",
  autoConnect = true,
}: UseNewsWebSocketOptions = {}): UseNewsWebSocketResult => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<number | null>(null);

  // Get the token from localStorage or passed prop
  const getToken = useCallback(() => {
    const rawToken = authToken || localStorage.getItem("access_token");
    // console.log("rawToken", rawToken);
    return rawToken?.replace(/^["'](.*)["']$/, "$1");
  }, [authToken]);

  // Generate WebSocket URL with client ID and token
  const getWebSocketUrl = useCallback(() => {
    const token = getToken();
    // console.log("token", token);
    if (!token) {
      throw new Error("Not authenticated");
    }
    const clientId = Math.floor(Math.random() * 1000000).toString();
    return `${baseUrl}/api/v1/news/ws/${clientId}?token=${token}`;
  }, [baseUrl, getToken]);

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
    connect,
    disconnect,
  };
};

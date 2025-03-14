import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";

import { NewsItem, WebSocketConnectionInfo } from "../types";

type UseNewsWebSocketOptions = {
  onMessage?: (news: NewsItem) => void;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  authToken?: string;
};

type UseNewsWebSocketResult = {
  isConnected: boolean;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  refreshConnection: () => Promise<void>;
};

/**
 * Custom hook for connecting to the news WebSocket API
 *
 * @param options Configuration options for the WebSocket connection
 * @returns WebSocket connection state and control functions
 */
export const useNewsWebSocket = ({
  onMessage,
  autoConnect = false,
  reconnectInterval = 5000,
  maxReconnectAttempts = 5,
  authToken,
}: UseNewsWebSocketOptions = {}): UseNewsWebSocketResult => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);

  // Clean up function to reset all WebSocket related state
  const cleanUp = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    // Clear any pending timeouts/intervals
    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (pingIntervalRef.current) {
      window.clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    setIsConnected(false);
  }, []);

  // Function to fetch WebSocket connection info from the backend
  const fetchWebSocketInfo = async (): Promise<WebSocketConnectionInfo> => {
    try {
      const apiBaseUrl = "http://localhost:8000/api/v1";

      // Get token from parameter or try to get from localStorage as fallback
      const token = authToken || localStorage.getItem("access_token");

      if (!token) {
        throw new Error("Not authenticated");
      }

      const response = await axios.get<WebSocketConnectionInfo>(
        `${apiBaseUrl}/news/ws-info`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          `Failed to get WebSocket info: ${error.response?.data?.detail || error.message}`
        );
      }
      throw new Error("Failed to get WebSocket info");
    }
  };

  const connect = useCallback(async () => {
    cleanUp(); // up any existing connection first
    setError(null);

    try {
      const wsInfo = await fetchWebSocketInfo();

      if (!wsInfo.websocket_url) {
        throw new Error("No WebSocket URL returned from the server");
      }

      // Construct the full WebSocket URL
      // The backend returns a path like "/api/v1/news/ws/123?token=xyz"
      // We need to prepend the WebSocket base URL
      const wsBaseUrl = "ws://localhost:8000";
      const wsUrl = `${wsBaseUrl}${wsInfo.websocket_url}`;

      console.log("Connecting to WebSocket URL:", wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Set up ping interval to keep the connection alive
        pingIntervalRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 30000); // every 30 seconds
      };

      ws.onclose = (event) => {
        setIsConnected(false);

        if (pingIntervalRef.current) {
          window.clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Attempt to reconnect if not closed cleanly and we haven't exceeded max attempts
        if (
          !event.wasClean &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current += 1;
          const delay =
            reconnectInterval * Math.pow(1.5, reconnectAttemptsRef.current - 1);

          setError(
            `Connection closed. Reconnecting in ${Math.round(delay / 1000)} seconds...`
          );

          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError(
            "Maximum reconnection attempts reached. Please try again later."
          );
        }
      };

      ws.onerror = (event) => {
        setError("WebSocket error occurred");
        console.error("WebSocket error:", event);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === "news" && message.data && onMessage) {
            onMessage(message.data);
          } else if (message.type === "pong") {
            // Received pong response, connection is alive
            console.debug("Received pong from server");
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "Failed to connect to WebSocket"
      );
      console.error("WebSocket connection error:", error);
    }
  }, [cleanUp, maxReconnectAttempts, onMessage, reconnectInterval]);

  const disconnect = useCallback(() => {
    cleanUp();
  }, [cleanUp]);

  const refreshConnection = useCallback(async () => {
    await disconnect();
    await connect();
  }, [connect, disconnect]);

  useEffect(() => {
    if (autoConnect) connect();
    return () => cleanUp();
  }, [autoConnect, cleanUp, connect]);

  return {
    isConnected,
    error,
    connect,
    disconnect,
    refreshConnection,
  };
};

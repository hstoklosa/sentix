import { useState, useEffect, useCallback } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { useLocalStorage } from "@/hooks/use-local-storage";

import { NewsItem } from "../types";

type UseNewsWebSocketOptions = {
  onMessage?: (news: NewsItem) => void;
  autoConnect?: boolean;
  baseUrl?: string;
};

type UseNewsWebSocketResult = {
  isConnected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
};

export const useNewsWebSocket = ({
  baseUrl = "ws://localhost:8000",
  onMessage,
  autoConnect = true,
}: UseNewsWebSocketOptions = {}): UseNewsWebSocketResult => {
  const [error, setError] = useState<string | null>(null);
  const [socketUrl, setSocketUrl] = useState<string | null>(null);
  const [manualConnect, setManualConnect] = useState<boolean>(!autoConnect);

  // Use useLocalStorage to get the latest access_token
  const [storedToken] = useLocalStorage<string>("access_token", "");
  const token = storedToken;

  // Generate WebSocket URL with client ID and token
  const generateWebSocketUrl = useCallback((): string | null => {
    if (!token) {
      return null;
    }
    const cleanToken = token.replace(/^['"](.*)['"]$/, "$1");
    const clientId = Math.floor(Math.random() * 1000000).toString();
    return `${baseUrl}/api/v1/news/ws/${clientId}?token=${cleanToken}`;
  }, [baseUrl, token]);

  // Set initial socket URL if autoConnect is true
  useEffect(() => {
    if (autoConnect && !socketUrl) {
      const url = generateWebSocketUrl();
      if (url) {
        setSocketUrl(url);
      } else {
        setError("Not authenticated");
      }
    }
  }, [autoConnect, generateWebSocketUrl, socketUrl]);

  // Reconnect if token changes
  useEffect(() => {
    if (autoConnect && token) {
      const url = generateWebSocketUrl();
      setSocketUrl(url);
    }
  }, [token, autoConnect, generateWebSocketUrl]);

  const { sendJsonMessage, readyState, getWebSocket } = useWebSocket(socketUrl, {
    onOpen: () => {
      console.log("Connected to WebSocket");
      setError(null);
    },
    onClose: (event) => {
      console.log(`WebSocket closed: ${event.code}`);
    },
    onError: (event) => {
      console.error("WebSocket error:", event);
      setError("WebSocket error occurred");
    },
    onMessage: (event) => {
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
    },
    shouldReconnect: () => !manualConnect,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
    retryOnError: true,
    filter: () => true,
  });

  // Setup ping interval
  useEffect(() => {
    if (readyState !== ReadyState.OPEN) {
      return;
    }

    const pingInterval = setInterval(() => {
      if (readyState === ReadyState.OPEN) {
        sendJsonMessage({ type: "ping" });
      }
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [readyState, sendJsonMessage]);

  // Check if connected
  const isConnected = readyState === ReadyState.OPEN;

  // Connect function
  const connect = useCallback(() => {
    setError(null);
    const url = generateWebSocketUrl();
    if (url) {
      setSocketUrl(url);
      setManualConnect(false);
    } else {
      setError("Not authenticated");
    }
  }, [generateWebSocketUrl]);

  // Disconnect function
  const disconnect = useCallback(() => {
    setManualConnect(true);
    // Close the current connection if it exists
    const ws = getWebSocket();
    if (ws) {
      ws.close();
    }
    setSocketUrl(null);
  }, [getWebSocket]);

  // Connect on mount if autoConnect is true
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    error,
    connect,
    disconnect,
  };
};

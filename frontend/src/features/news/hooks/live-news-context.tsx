import {
  useState,
  useEffect,
  createContext,
  useContext,
  ReactNode,
  useCallback,
  useRef,
} from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";

import { useLocalStorage } from "@/hooks/use-local-storage";
import useAuth from "@/hooks/use-auth";

import { NewsItem } from "../types";

type LiveNewsContextType = {
  isConnected: boolean;
  error: string | null;
  registerMessageHandler: (handler: (news: NewsItem) => void) => void;
  unregisterMessageHandler: () => void;
};

const LiveNewsContext = createContext<LiveNewsContextType>({
  isConnected: false,
  error: null,
  registerMessageHandler: () => {},
  unregisterMessageHandler: () => {},
});

type LiveNewsProviderProps = {
  baseUrl?: string;
  onMessage?: (news: NewsItem) => void;
  children: ReactNode;
};

export const LiveNewsProvider = ({
  baseUrl = "ws://localhost:8000",
  onMessage,
  children,
}: LiveNewsProviderProps) => {
  const [error, setError] = useState<string | null>(null);
  const messageHandlerRef = useRef<((news: NewsItem) => void) | null>(null);

  const [accessToken] = useLocalStorage<string>("access_token", "");
  const { user } = useAuth();

  const handleMessage = useCallback(
    (news: NewsItem) => {
      // Use the registered handler if available, otherwise fall back to onMessage prop
      if (messageHandlerRef.current) {
        messageHandlerRef.current(news);
      } else if (onMessage) {
        onMessage(news);
      }
    },
    [onMessage]
  );

  const registerMessageHandler = useCallback(
    (handler: (news: NewsItem) => void) => {
      messageHandlerRef.current = handler;
    },
    []
  );

  const unregisterMessageHandler = useCallback(() => {
    messageHandlerRef.current = null;
  }, []);

  const { sendJsonMessage, readyState } = useWebSocket(
    `${baseUrl}/api/v1/news/ws/${user?.id}?token=${accessToken}`,
    {
      onOpen: () => {
        setError(null);
      },
      onClose: () => {},
      onError: () => {
        setError("WebSocket error occurred");
      },
      onMessage: (event) => {
        try {
          const message = JSON.parse(event.data);
          switch (message.type) {
            case "news":
              if (message.data) handleMessage(message.data);
              break;
            case "pong":
              break;
            case "error":
              setError(message.message || "An error occurred");
              break;
          }
        } catch (err) {
          setError("Error parsing WebSocket message");
        }
      },
      shouldReconnect: () => true,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
      retryOnError: true,
      filter: () => true,
    }
  );

  // Ping interval (keep connection alive)
  useEffect(() => {
    if (readyState !== ReadyState.OPEN) return;

    const pingInterval = setInterval(() => {
      if (readyState === ReadyState.OPEN) {
        sendJsonMessage({ type: "ping" });
      }
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [readyState, sendJsonMessage]);

  return (
    <LiveNewsContext.Provider
      value={{
        isConnected: readyState === ReadyState.OPEN,
        error,
        registerMessageHandler,
        unregisterMessageHandler,
      }}
    >
      {children}
    </LiveNewsContext.Provider>
  );
};

export const useLiveNews = () => {
  const context = useContext(LiveNewsContext);
  if (context === undefined) {
    throw new Error("useLiveNews must be used within a LiveNewsProvider");
  }
  return context;
};

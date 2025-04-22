import { createContext, useContext, ReactNode } from "react";
import { useNewsWebSocket } from "../hooks/use-news-websocket";
import { NewsItem } from "../types";

type WebSocketContextType = {
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

const WebSocketContext = createContext<WebSocketContextType>({
  isConnected: false,
  error: null,
  currentProvider: null,
  availableProviders: [],
  connect: () => {},
  disconnect: () => {},
  subscribe: () => {},
  unsubscribe: () => {},
  refreshProviders: () => {},
});

type WebSocketProviderProps = {
  children: ReactNode;
  onMessage?: (news: NewsItem) => void;
  authToken?: string;
  baseUrl?: string;
  defaultProvider?: string;
};

export const WebSocketProvider = ({
  children,
  onMessage,
  authToken,
  baseUrl,
  defaultProvider,
}: WebSocketProviderProps) => {
  const {
    isConnected,
    error,
    currentProvider,
    availableProviders,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    refreshProviders,
  } = useNewsWebSocket({
    onMessage,
    autoConnect: true,
    authToken,
    baseUrl,
    defaultProvider,
  });

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        error,
        currentProvider,
        availableProviders,
        connect,
        disconnect,
        subscribe,
        unsubscribe,
        refreshProviders,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error("useWebSocketContext must be used within a WebSocketProvider");
  }
  return context;
};

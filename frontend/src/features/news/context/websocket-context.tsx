import { createContext, useContext, ReactNode, useState, useEffect } from "react";
import { useNewsWebSocket } from "../hooks/use-news-websocket";
import { NewsItem } from "../types";

// Context type definition
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

// Create context with default values
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

// Props for the provider component
type WebSocketProviderProps = {
  children: ReactNode;
  onMessage?: (news: NewsItem) => void;
  authToken?: string;
  baseUrl?: string;
  defaultProvider?: string;
};

// Provider component
export const WebSocketProvider = ({
  children,
  onMessage,
  authToken,
  baseUrl,
  defaultProvider,
}: WebSocketProviderProps) => {
  // Use the hook internally
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

  // Provide the WebSocket state and functions to all children
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

// Custom hook to use the WebSocket context
export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error("useWebSocketContext must be used within a WebSocketProvider");
  }
  return context;
};

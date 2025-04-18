import { createContext, useContext, ReactNode, useState, useEffect } from "react";
import { useNewsWebSocket } from "../hooks/use-news-websocket";
import { NewsItem } from "../types";

// Context type definition
type WebSocketContextType = {
  isConnected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
};

// Create context with default values
const WebSocketContext = createContext<WebSocketContextType>({
  isConnected: false,
  error: null,
  connect: () => {},
  disconnect: () => {},
});

// Props for the provider component
type WebSocketProviderProps = {
  children: ReactNode;
  onMessage?: (news: NewsItem) => void;
  authToken?: string;
  baseUrl?: string;
};

// Provider component
export const WebSocketProvider = ({
  children,
  onMessage,
  authToken,
  baseUrl,
}: WebSocketProviderProps) => {
  // Use the hook internally
  const { isConnected, error, connect, disconnect } = useNewsWebSocket({
    onMessage,
    autoConnect: true,
    authToken,
    baseUrl,
  });

  // Provide the WebSocket state and functions to all children
  return (
    <WebSocketContext.Provider value={{ isConnected, error, connect, disconnect }}>
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

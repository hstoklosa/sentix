import { useCallback, createContext, useContext, ReactNode } from "react";
import useWebSocket from "react-use-websocket";

import { useLocalStorage } from "@/hooks/use-local-storage";
import useAuth from "@/hooks/use-auth";

import { useNewsWebSocket } from "../hooks/use-news-websocket";
import { NewsItem } from "../types";

type LiveNewsContextType = {
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

const LiveNewsContext = createContext<LiveNewsContextType>({
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

type LiveNewsProviderProps = {
  children: ReactNode;
  onMessage?: (news: NewsItem) => void;
  authToken?: string;
  baseUrl?: string;
  defaultProvider?: string;
};

export const LiveNewsProvider = ({
  children,
  onMessage,
  authToken,
  baseUrl,
  defaultProvider,
}: LiveNewsProviderProps) => {
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

  const [accessToken, _] = useLocalStorage("access_token", "");
  const { user, status: authStatus } = useAuth();

  const getSocketUrl = useCallback(() => {
    return `ws://localhost:8000/api/v1/news/ws/${user?.id}?token=${accessToken}`;
  }, [user, accessToken]);

  return (
    <LiveNewsContext.Provider
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
    </LiveNewsContext.Provider>
  );
};

export const useLiveNewsContext = () => {
  const context = useContext(LiveNewsContext);
  if (context === undefined) {
    throw new Error("useLiveNewsContext must be used within a LiveNewsProvider");
  }
  return context;
};

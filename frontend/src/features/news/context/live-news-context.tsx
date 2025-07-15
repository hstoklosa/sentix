import { useState, useCallback, createContext, useContext, ReactNode } from "react";
import useWebSocket from "react-use-websocket";

import { useLocalStorage } from "@/hooks/use-local-storage";
import useAuth from "@/hooks/use-auth";

import { useNewsWebSocket } from "../hooks/use-news-websocket";
import { NewsItem } from "../types";

type LiveNewsContextType = {
  isConnected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
};

const LiveNewsContext = createContext<LiveNewsContextType>({
  isConnected: false,
  error: null,
  connect: () => {},
  disconnect: () => {},
});

type LiveNewsProviderProps = {
  children: ReactNode;
  onMessage?: (news: NewsItem) => void;
  baseUrl?: string;
};

export const LiveNewsProvider = ({
  children,
  onMessage,
  baseUrl,
}: LiveNewsProviderProps) => {
  const { isConnected, error, connect, disconnect } = useNewsWebSocket({
    onMessage,
    autoConnect: true,
    baseUrl,
  });

  // const [error, setError] = useState<string | null>(null);

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
        connect,
        disconnect,
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

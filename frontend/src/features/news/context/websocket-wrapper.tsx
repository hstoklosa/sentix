import { ReactNode } from "react";
import { WebSocketProvider } from "./websocket-context";
import { useUpdatePostsCache } from "../api";

type WebSocketProviderWrapperProps = {
  children: ReactNode;
};

/**
 * A wrapper component that provides WebSocket context
 * This ensures the WebSocketProvider is created after React Query is initialized
 */
export const WebSocketProviderWrapper = ({
  children,
}: WebSocketProviderWrapperProps) => {
  const updatePostsCache = useUpdatePostsCache();

  return (
    <WebSocketProvider onMessage={updatePostsCache}>{children}</WebSocketProvider>
  );
};

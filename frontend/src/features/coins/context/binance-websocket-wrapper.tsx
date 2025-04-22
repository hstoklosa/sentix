import { ReactNode } from "react";
import { BinanceWebSocketProvider } from "./binance-websocket-context";

type BinanceWebSocketProviderWrapperProps = {
  children: ReactNode;
};

/**
 * A wrapper component that provides Binance WebSocket context
 * This ensures the BinanceWebSocketProvider is created after React Query is initialized
 */
export const BinanceWebSocketProviderWrapper = ({
  children,
}: BinanceWebSocketProviderWrapperProps) => {
  return <BinanceWebSocketProvider>{children}</BinanceWebSocketProvider>;
};

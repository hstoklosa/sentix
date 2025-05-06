import { createContext, useContext, ReactNode, useState, useMemo } from "react";
import useBinanceWebSocket from "../hooks/use-binance-websocket";

type BinanceWebSocketContextType = {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
};

const BinanceWebSocketContext = createContext<BinanceWebSocketContextType>({
  isConnected: false,
  connect: () => {},
  disconnect: () => {},
});

export const BinanceWebSocketProvider = ({ children }: { children: ReactNode }) => {
  const [isConnected, setIsConnected] = useState(false);

  // Use the hook internally with a callback for connection status
  const binanceWS = useBinanceWebSocket({
    onConnectionChange: setIsConnected,
    autoConnect: true,
  });

  // Provide the WebSocket state and functions to all children
  const value = useMemo(
    () => ({
      isConnected,
      connect: binanceWS.connect,
      disconnect: binanceWS.disconnect,
    }),
    [isConnected, binanceWS]
  );

  return (
    <BinanceWebSocketContext.Provider value={value}>
      {children}
    </BinanceWebSocketContext.Provider>
  );
};

export const useBinanceWebSocketContext = () => {
  const context = useContext(BinanceWebSocketContext);
  if (context === undefined) {
    throw new Error(
      "useBinanceWebSocketContext must be used within a BinanceWebSocketProvider"
    );
  }
  return context;
};

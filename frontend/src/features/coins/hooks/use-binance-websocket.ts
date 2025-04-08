import { useEffect, useRef, useState } from "react";

const BINANCE_WS_URL = "wss://stream.binance.com:9443/ws";

type PriceUpdateCallback = (
  symbol: string,
  price: number,
  changePercent: number
) => void;

const useBinanceWebSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const subscribedSymbols = useRef<Set<string>>(new Set());
  const callbacksRef = useRef<PriceUpdateCallback[]>([]);

  // Connect to WebSocket
  useEffect(() => {
    const connect = () => {
      wsRef.current = new WebSocket(BINANCE_WS_URL);

      wsRef.current.onopen = () => {
        console.log("Connected to Binance WebSocket");
        setIsConnected(true);

        // Resubscribe to all symbols
        if (subscribedSymbols.current.size > 0) {
          const symbols = Array.from(subscribedSymbols.current);
          subscribeToSymbols(symbols);
        }
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Handle ticker data
          if (data.s && data.c && data.P) {
            const symbol = data.s;
            const price = parseFloat(data.c);
            const changePercent = parseFloat(data.P);

            // Notify all callbacks
            callbacksRef.current.forEach((callback) => {
              callback(symbol, price, changePercent);
            });
          }
        } catch (error) {
          console.error("Error parsing Binance message:", error);
        }
      };

      wsRef.current.onclose = () => {
        console.log("Binance WebSocket closed");
        setIsConnected(false);
      };

      wsRef.current.onerror = (error) => {
        console.error("Binance WebSocket error:", error);
      };
    };

    connect();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  // Subscribe to symbols
  const subscribeToSymbols = (symbols: string[]) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const message = {
      method: "SUBSCRIBE",
      params: symbols.map((s) => `${s.toLowerCase()}@ticker`),
      id: Date.now(),
    };

    wsRef.current.send(JSON.stringify(message));

    // Add to tracked symbols
    symbols.forEach((symbol) => subscribedSymbols.current.add(symbol));
  };

  // Unsubscribe from symbols
  const unsubscribeFromSymbols = (symbols: string[]) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const message = {
      method: "UNSUBSCRIBE",
      params: symbols.map((s) => `${s.toLowerCase()}@ticker`),
      id: Date.now(),
    };

    wsRef.current.send(JSON.stringify(message));

    // Remove from tracked symbols
    symbols.forEach((symbol) => subscribedSymbols.current.delete(symbol));
  };

  // Register a callback for price updates
  const onPriceUpdate = (callback: PriceUpdateCallback) => {
    callbacksRef.current.push(callback);

    // Return function to unregister callback
    return () => {
      callbacksRef.current = callbacksRef.current.filter((cb) => cb !== callback);
    };
  };

  return {
    isConnected,
    subscribeToSymbols,
    unsubscribeFromSymbols,
    onPriceUpdate,
  };
};

export default useBinanceWebSocket;

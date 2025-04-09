import { useEffect, useRef, useCallback } from "react";

import { useTokenPrice } from "../context/token-price-context";

const BINANCE_WS_URL = "wss://stream.binance.com:9443/ws";

type PriceUpdateCallback = (
  symbol: string,
  price: number,
  changePercent: number
) => void;

class BinanceWebSocketManager {
  private static instance: BinanceWebSocketManager;

  private socket: WebSocket | null;
  private subscriptions: Set<string>;
  private updateTokenPrice: PriceUpdateCallback;

  private constructor(updateFn: PriceUpdateCallback) {
    this.socket = null;
    this.subscriptions = new Set();
    this.updateTokenPrice = updateFn;
  }

  public static getInstance(
    updateFn: PriceUpdateCallback
  ): BinanceWebSocketManager {
    if (!BinanceWebSocketManager.instance) {
      BinanceWebSocketManager.instance = new BinanceWebSocketManager(updateFn);
    }

    return BinanceWebSocketManager.instance;
  }

  public connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) return;

    this.socket = new WebSocket(BINANCE_WS_URL);

    this.socket.onopen = () => {
      console.log("Connected to Binance WebSocket");
      this.resubscribeAll();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.s && data.c && data.P) {
          const symbol = data.s;
          const price = parseFloat(data.c);
          const changePercent = parseFloat(data.P);
          this.updateTokenPrice(symbol, price, changePercent);
        }
      } catch (error) {
        console.error("Error parsing Binance message:", error);
      }
    };

    this.socket.onclose = () => {
      console.log("Binance WebSocket closed");
    };

    this.socket.onerror = (error) => {
      console.error("Binance WebSocket error:", error);
      this.socket?.close();
    };
  }

  public subscribe(symbol: string): void {
    const formattedSymbol = this.formatSymbol(symbol);

    if (this.subscriptions.has(formattedSymbol)) return;
    this.subscriptions.add(formattedSymbol);

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.sendSubscription(formattedSymbol);
    } else if (!this.socket || this.socket.readyState === WebSocket.CLOSED) {
      this.connect();
    }
  }

  public unsubscribe(symbol: string): void {
    const formattedSymbol = this.formatSymbol(symbol);

    if (!this.subscriptions.has(formattedSymbol)) return;
    this.subscriptions.delete(formattedSymbol);

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.sendUnsubscription(formattedSymbol);
    }

    // Close socket if no more subscriptions
    if (this.subscriptions.size === 0) {
      this.disconnect();
    }
  }

  private formatSymbol(symbol: string): string {
    // Convert to lowercase and assume USDT trading pair
    return `${symbol.toLowerCase()}usdt`;
  }

  private sendSubscription(formattedSymbol: string): void {
    const subscribeMsg = {
      method: "SUBSCRIBE",
      params: [`${formattedSymbol}@ticker`],
      id: Date.now(),
    };

    this.socket?.send(JSON.stringify(subscribeMsg));
  }

  private sendUnsubscription(formattedSymbol: string): void {
    const unsubscribeMsg = {
      method: "UNSUBSCRIBE",
      params: [`${formattedSymbol}@ticker`],
      id: Date.now(),
    };

    this.socket?.send(JSON.stringify(unsubscribeMsg));
  }

  private resubscribeAll(): void {
    if (this.subscriptions.size === 0) return;

    const subscribeMsg = {
      method: "SUBSCRIBE",
      params: Array.from(this.subscriptions).map((s) => `${s}@ticker`),
      id: Date.now(),
    };

    this.socket?.send(JSON.stringify(subscribeMsg));
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;
      this.socket.onopen = null;

      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.close();
      }

      this.socket = null;
    }

    this.subscriptions.clear();
  }
}

const useBinanceWebSocket = () => {
  const { addOrUpdatePrice } = useTokenPrice();
  const managerRef = useRef<BinanceWebSocketManager | null>(null);

  const stableSubscribeToSymbol = useRef<(symbol: string) => void>(
    (_: string) => {}
  );

  const stableUnsubscribeFromSymbol = useRef<(symbol: string) => void>(
    (_: string) => {}
  );

  useEffect(() => {
    // Initialise singleton manager on component mount
    const manager = BinanceWebSocketManager.getInstance(
      (symbol, price, changePercent) => {
        addOrUpdatePrice(symbol, price, changePercent);
      }
    );

    managerRef.current = manager;

    // Create stable reference to subscription functions
    stableSubscribeToSymbol.current = (symbol: string) => {
      if (!symbol) return;
      managerRef.current?.subscribe(symbol);
    };

    stableUnsubscribeFromSymbol.current = (symbol: string) => {
      if (!symbol) return;
      managerRef.current?.unsubscribe(symbol);
    };
    // Do not disconnect since other components might be using the manager
    // The manager itself will handle cleanup when no more subscriptions
    return () => {};
  }, [addOrUpdatePrice]);

  // Wrap the ref access in stable function references
  const subscribeToSymbol = useCallback((symbol: string) => {
    stableSubscribeToSymbol.current(symbol);
  }, []);

  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    stableUnsubscribeFromSymbol.current(symbol);
  }, []);

  return {
    subscribeToSymbol,
    unsubscribeFromSymbol,
  };
};

export default useBinanceWebSocket;

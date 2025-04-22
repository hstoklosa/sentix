import { useEffect, useRef, useCallback, useState } from "react";

import { usePriceStore } from "./use-price-store";

const BINANCE_WS_URL = "wss://stream.binance.com:9443/ws";

type PriceUpdateCallback = (
  symbol: string,
  price: number,
  changePercent: number
) => void;

type ConnectionStatusCallback = (isConnected: boolean) => void;

type UseBinanceWebSocketOptions = {
  onConnectionChange?: ConnectionStatusCallback;
  autoConnect?: boolean;
};

/**
 * Singleton WebSocket manager for Binance's pricing data, which
 * provides efficient handling of multiple symbol subscriptions.
 */
class BinanceWebSocketManager {
  private static instance: BinanceWebSocketManager;

  private socket: WebSocket | null;
  private subscriptions: Set<string>;
  private updateTokenPrice: PriceUpdateCallback;
  private pendingSubscriptions: Set<string>;
  private pendingUnsubscriptions: Set<string>;
  private batchTimeoutId: number | null;
  private isConnecting: boolean;
  private connectionStatusCallback: ConnectionStatusCallback | null;

  private constructor(updateFn: PriceUpdateCallback) {
    this.socket = null;
    this.subscriptions = new Set();
    this.updateTokenPrice = updateFn;
    this.pendingSubscriptions = new Set();
    this.pendingUnsubscriptions = new Set();
    this.batchTimeoutId = null;
    this.isConnecting = false;
    this.connectionStatusCallback = null;
  }

  public static getInstance(
    updateFn: PriceUpdateCallback
  ): BinanceWebSocketManager {
    if (!BinanceWebSocketManager.instance) {
      BinanceWebSocketManager.instance = new BinanceWebSocketManager(updateFn);
    }

    return BinanceWebSocketManager.instance;
  }

  public setConnectionStatusCallback(
    callback: ConnectionStatusCallback | null
  ): void {
    this.connectionStatusCallback = callback;

    // Update the callback with current connection status
    if (callback && this.socket && this.socket.readyState === WebSocket.OPEN) {
      callback(true);
    } else if (callback) {
      callback(false);
    }
  }

  public connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN || this.isConnecting) return;

    this.isConnecting = true;
    this.socket = new WebSocket(BINANCE_WS_URL);

    this.socket.onopen = () => {
      // Notify connection status change
      this.isConnecting = false;
      if (this.connectionStatusCallback) {
        this.connectionStatusCallback(true);
      }

      // Process any pending subscriptions that accumulated while connecting
      this.processBatchedSubscriptions();
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
      // Notify connection status change
      this.isConnecting = false;
      this.socket = null;
      if (this.connectionStatusCallback) {
        this.connectionStatusCallback(false);
      }
    };

    this.socket.onerror = (error) => {
      console.error("Binance WebSocket error:", error);
      this.isConnecting = false;
      this.socket?.close();

      // Notify connection status change
      if (this.connectionStatusCallback) {
        this.connectionStatusCallback(false);
      }
    };
  }

  /**
   * Add a subscription - batches multiple subscription requests
   */
  public subscribe(symbol: string): void {
    if (!symbol) return;

    const formattedSymbol = this.formatSymbol(symbol);

    // Skip if already subscribed or pending subscription
    if (
      this.subscriptions.has(formattedSymbol) ||
      this.pendingSubscriptions.has(formattedSymbol)
    ) {
      return;
    }

    // If in pending unsubscriptions, just remove it from there
    if (this.pendingUnsubscriptions.has(formattedSymbol)) {
      this.pendingUnsubscriptions.delete(formattedSymbol);
      return;
    }

    this.pendingSubscriptions.add(formattedSymbol);
    this.scheduleBatch();
  }

  /**
   * Remove a subscription - batches multiple unsubscription requests
   */
  public unsubscribe(symbol: string): void {
    if (!symbol) return;

    const formattedSymbol = this.formatSymbol(symbol);

    // Already unsubscribed or pending unsubscription
    if (
      !this.subscriptions.has(formattedSymbol) &&
      !this.pendingSubscriptions.has(formattedSymbol)
    ) {
      return;
    }

    if (this.pendingSubscriptions.has(formattedSymbol)) {
      this.pendingSubscriptions.delete(formattedSymbol);
      return;
    }

    this.pendingUnsubscriptions.add(formattedSymbol);
    this.scheduleBatch();
  }

  /**
   * Schedule a batch operation with debouncing
   */
  private scheduleBatch(): void {
    if (this.batchTimeoutId !== null) {
      window.clearTimeout(this.batchTimeoutId);
    }

    this.batchTimeoutId = window.setTimeout(() => {
      this.batchTimeoutId = null;
      this.processBatchedSubscriptions();
    }, 100); // Batch window of 100ms
  }

  /**
   * Process all pending subscriptions and unsubscriptions in a single batch
   */
  private processBatchedSubscriptions(): void {
    // Don't process empty batches
    if (
      this.pendingSubscriptions.size === 0 &&
      this.pendingUnsubscriptions.size === 0
    ) {
      return;
    }

    // Ensure socket is connected
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      if (!this.isConnecting) {
        this.connect();
      }
      return;
    }

    // Process subscriptions
    if (this.pendingSubscriptions.size > 0) {
      const symbols = Array.from(this.pendingSubscriptions);

      const batchSubscribe = {
        method: "SUBSCRIBE",
        params: symbols.map((s) => `${s}@ticker`),
        id: Date.now(),
      };

      this.socket.send(JSON.stringify(batchSubscribe));

      // Add to active subscriptions
      symbols.forEach((symbol) => {
        this.subscriptions.add(symbol);
      });
      this.pendingSubscriptions.clear();
    }

    // Process unsubscriptions
    if (this.pendingUnsubscriptions.size > 0) {
      const symbols = Array.from(this.pendingUnsubscriptions);

      const batchUnsubscribe = {
        method: "UNSUBSCRIBE",
        params: symbols.map((s) => `${s}@ticker`),
        id: Date.now(),
      };

      this.socket.send(JSON.stringify(batchUnsubscribe));

      // Remove from active subscriptions
      symbols.forEach((symbol) => {
        this.subscriptions.delete(symbol);
      });
      this.pendingUnsubscriptions.clear();
    }

    // Close socket if no more subscriptions
    if (this.subscriptions.size === 0) {
      console.log(`[BinanceWS] No active subscriptions, closing connection`);
      this.disconnect();
    } else {
      console.log(
        `[BinanceWS] Active subscriptions remaining: ${this.subscriptions.size}`
      );
    }
  }

  private formatSymbol(symbol: string): string {
    // Convert to lowercase and assume USDT trading pair
    return `${symbol.toLowerCase()}usdt`;
  }

  private resubscribeAll(): void {
    if (this.subscriptions.size === 0) return;

    const symbols = Array.from(this.subscriptions);
    const subscribeMsg = {
      method: "SUBSCRIBE",
      params: symbols.map((s) => `${s}@ticker`),
      id: Date.now(),
    };

    this.socket?.send(JSON.stringify(subscribeMsg));
    console.log(
      `[BinanceWS] Resubscribed to ${symbols.length} symbols: ${symbols.join(", ")}`
    );
  }

  public disconnect(): void {
    if (this.batchTimeoutId !== null) {
      window.clearTimeout(this.batchTimeoutId);
      this.batchTimeoutId = null;
    }

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
    this.pendingSubscriptions.clear();
    this.pendingUnsubscriptions.clear();
    this.isConnecting = false;

    // Notify connection status change
    if (this.connectionStatusCallback) {
      this.connectionStatusCallback(false);
    }

    console.log(`[BinanceWS] Disconnected and cleared all subscriptions`);
  }

  public isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

/**
 * Hook for interacting with the BinanceWebSocketManager
 * Provides stable subscription methods for components
 */
const useBinanceWebSocket = (options: UseBinanceWebSocketOptions = {}) => {
  const { updatePrice } = usePriceStore();
  const managerRef = useRef<BinanceWebSocketManager | null>(null);
  const { onConnectionChange, autoConnect = false } = options;

  const stableSubscribeToSymbol = useRef<(symbol: string) => void>(
    (_: string) => {}
  );

  const stableUnsubscribeFromSymbol = useRef<(symbol: string) => void>(
    (_: string) => {}
  );

  const stableConnect = useRef<() => void>(() => {});
  const stableDisconnect = useRef<() => void>(() => {});

  useEffect(() => {
    // Initialise singleton manager on component mount
    const manager = BinanceWebSocketManager.getInstance(
      (symbol, price, changePercent) => {
        updatePrice(symbol, price, changePercent);
      }
    );

    managerRef.current = manager;

    // Set connection status callback if provided
    if (onConnectionChange) {
      manager.setConnectionStatusCallback(onConnectionChange);
    }

    // Create stable reference to subscription functions
    stableSubscribeToSymbol.current = (symbol: string) => {
      if (!symbol) return;
      managerRef.current?.subscribe(symbol);
    };

    stableUnsubscribeFromSymbol.current = (symbol: string) => {
      if (!symbol) return;
      managerRef.current?.unsubscribe(symbol);
    };

    stableConnect.current = () => {
      managerRef.current?.connect();
    };

    stableDisconnect.current = () => {
      managerRef.current?.disconnect();
    };

    // Auto-connect if specified
    if (autoConnect) {
      manager.connect();
    }

    // Cleanup
    return () => {
      if (onConnectionChange) {
        manager.setConnectionStatusCallback(null);
      }
    };
  }, [updatePrice, onConnectionChange, autoConnect]);

  // Wrap the ref access in stable function references
  const subscribeToSymbol = useCallback((symbol: string) => {
    stableSubscribeToSymbol.current(symbol);
  }, []);

  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    stableUnsubscribeFromSymbol.current(symbol);
  }, []);

  const connect = useCallback(() => {
    stableConnect.current();
  }, []);

  const disconnect = useCallback(() => {
    stableDisconnect.current();
  }, []);

  return {
    subscribeToSymbol,
    unsubscribeFromSymbol,
    connect,
    disconnect,
  };
};

export default useBinanceWebSocket;

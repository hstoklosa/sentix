/**
 * Types for the news feature
 */

export interface NewsItem {
  title: string;
  body: string;
  source: string;
  time: string;
  url?: string;
  image?: string;
  icon?: string;
  coins?: string[];
  feed?: string;
}

export interface WebSocketConnectionInfo {
  websocket_url: string;
}

export interface WebSocketMessage {
  type: "news" | "pong";
  data?: NewsItem;
}

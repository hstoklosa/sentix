export interface NewsItem {
  title: string;
  body: string;
  source: string;
  time: string;
  url: string;
  image?: string;
  icon?: string;
  coins: string[];
  feed: string;
}

export interface NewsMessage {
  type: "news";
  data?: NewsItem;
}

export interface PongMessage {
  type: "pong";
}

export type WebSocketMessage = NewsMessage | PongMessage;

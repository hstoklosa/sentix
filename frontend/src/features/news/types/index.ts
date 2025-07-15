import { Entity, PaginatedResponse } from "@/types/api";

export type NewsItem = Entity<{
  title: string;
  body: string;
  source: string;
  time: string;
  url: string;
  image_url?: string;
  icon_url?: string;
  coins: {
    id: number;
    symbol: string;
    name: string;
    image_url?: string;
    price_usd?: number;
    price_timestamp?: string;
  }[];
  feed: string;
  _type: string;
  is_bookmarked: boolean;
  bookmark_id?: number;
  sentiment: string;
  score: number;
}>;

export type NewsMessage = { type: "news"; data: NewsItem };
export type PongMessage = { type: "pong" };
export type WebSocketMessage = NewsMessage | PongMessage;

export type NewsFeedResponse = PaginatedResponse<NewsItem>;

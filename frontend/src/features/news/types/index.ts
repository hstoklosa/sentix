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
  }[];
  feed: string;
  _type: string;
  is_bookmarked: boolean;
}>;

export type NewsMessage = { type: "news"; data: NewsItem };
export type PongMessage = { type: "pong" };
export type WebSocketMessage = NewsMessage | PongMessage;

export type NewsFeedResponse = PaginatedResponse<NewsItem>;

export interface SentimentStats {
  positive: number;
  negative: number;
  neutral: number;
}

export interface TrendingCoin {
  id: number;
  symbol: string;
  name?: string;
  image_url?: string;
  mention_count: number;
  sentiment_stats: SentimentStats;
}

export interface TrendingCoinsResponse {
  items: TrendingCoin[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface SentimentDataPoint {
  timestamp: string;
  average_sentiment: number;
  mentions: number;
  price: number | null;
  divergence: "bullish" | "bearish" | null;
}

export interface SentimentDivergenceProps {
  coinId: string;
  days?: number | "max";
  interval?: "daily" | "hourly";
  className?: string;
}

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

export type MarketStats = {
  total_market_cap: number;
  total_market_cap_24h_change: number;
  total_volume_24h: number;
  total_volume_24h_change: number;
  btc_dominance: number;
  eth_dominance: number;
  btc_dominance_24h_change: number;
  eth_dominance_24h_change: number;
  fear_and_greed_index: number;
  market_sentiment: string;
};

export type ChartDataPoint = {
  timestamp: number;
  value: number;
};

export type MarketChartData = {
  prices: ChartDataPoint[];
  market_caps: ChartDataPoint[];
  volumes: ChartDataPoint[];
};

export type ChartInterval = "daily" | "hourly";
export type ChartPeriod = 1 | 7 | 14 | 30 | 90 | 180 | 365 | "max" | "ytd";

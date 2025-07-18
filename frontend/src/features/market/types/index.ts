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

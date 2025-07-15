import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";

import type { SentimentDataPoint } from "../types";

const getSentimentDivergence = async (
  coinId: string,
  days: number | "max" = 30,
  interval: "daily" | "hourly" = "daily"
): Promise<SentimentDataPoint[]> => {
  return await api.get(`/market/coins/${coinId}/sentiment-divergence`, {
    params: { days, interval },
  });
};

export const useGetSentimentDivergence = (
  coinId: string,
  days: number | "max" = 30,
  interval: "daily" | "hourly" = "daily",
  config?: QueryConfig<typeof getSentimentDivergence>
) => {
  return useQuery({
    queryKey: ["sentiment-divergence", coinId, days, interval],
    queryFn: () => getSentimentDivergence(coinId, days, interval),
    ...config,
  });
};

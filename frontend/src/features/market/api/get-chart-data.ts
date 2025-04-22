import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";

import { MarketChartData, ChartInterval, ChartPeriod } from "../types";

type GetChartDataParams = {
  coinId: string;
  days?: ChartPeriod;
  interval?: ChartInterval;
};

const getChartData = async ({
  coinId,
  days = 30,
  interval = "daily",
}: GetChartDataParams): Promise<MarketChartData> => {
  return api.get(`/market/coins/${coinId}/chart`, {
    params: { days, interval },
  });
};

export const useGetChartData = (
  params: GetChartDataParams,
  config?: QueryConfig<typeof getChartData>
) => {
  return useQuery({
    queryKey: ["chart-data", params.coinId, params.days, params.interval],
    queryFn: () => getChartData(params),
    ...config,
  });
};

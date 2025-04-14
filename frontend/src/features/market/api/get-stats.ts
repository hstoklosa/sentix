import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";

import { MarketStats } from "../types";

const getStats = async (): Promise<MarketStats> => {
  return api.get("/market");
};

export const useGetStats = (config?: QueryConfig<typeof getStats>) => {
  return useQuery({
    queryKey: ["market-stats"],
    queryFn: getStats,
    ...config,
  });
};

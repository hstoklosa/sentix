import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";
import { PaginationParams } from "@/types/api";

import { TrendingCoinsResponse } from "../types";

const DEFAULT_PAGE_SIZE = 20;
const INITIAL_PARAMS = {
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
};

export const getTrendingCoins = async (
  params: PaginationParams = INITIAL_PARAMS
): Promise<TrendingCoinsResponse> => {
  return await api.get("/trending/coins", {
    params: {
      page: params.page,
      page_size: params.page_size,
    },
  });
};

export const useGetTrendingCoins = (
  params: PaginationParams = INITIAL_PARAMS,
  config?: QueryConfig<typeof getTrendingCoins>
) => {
  return useQuery({
    queryKey: ["trending", "coins", params],
    queryFn: () => getTrendingCoins(params),
    ...config,
  });
};

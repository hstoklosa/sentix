import { useQuery, useInfiniteQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";
import { PaginationParams } from "@/types/api";

import { WatchlistCoin } from "../types";

const DEFAULT_PAGE_SIZE = 20;
const INITIAL_PARAMS = {
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
};

export interface CoinsResponse {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
  items: WatchlistCoin[];
}

const getCoins = async (
  params: PaginationParams = INITIAL_PARAMS
): Promise<CoinsResponse> => {
  return api.get("/market/coins", {
    params: {
      page: params.page,
      page_size: params.page_size,
    },
  });
};

export const useGetCoins = (config?: QueryConfig<typeof getCoins>) => {
  return useQuery({
    queryKey: ["coins"],
    queryFn: () => getCoins(),
    ...config,
  });
};

export const useGetInfiniteCoins = (
  pageSize: number = DEFAULT_PAGE_SIZE,
  config?: QueryConfig<typeof getCoins>
) => {
  return useInfiniteQuery({
    queryKey: ["coins", "list", { pageSize }],
    queryFn: ({ pageParam = 1 }) =>
      getCoins({ page: pageParam, page_size: pageSize }),
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
    ...config,
  });
};

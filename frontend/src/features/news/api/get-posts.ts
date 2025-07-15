import { useQueryClient, useInfiniteQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";
import { PaginationParams } from "@/types/api";

import { NewsItem, NewsFeedResponse } from "../types";

const DEFAULT_PAGE_SIZE = 20;

interface ExtendedPaginationParams extends PaginationParams {
  start_date?: string;
  end_date?: string;
  coin?: string;
}

const INITIAL_PARAMS: ExtendedPaginationParams = {
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
};

export const getPosts = async (
  params: ExtendedPaginationParams = INITIAL_PARAMS
): Promise<NewsFeedResponse> => {
  const queryParams: any = {
    page: params.page,
    page_size: params.page_size,
  };

  // Only include date parameters if they are provided
  if (params.start_date) {
    queryParams.start_date = params.start_date;
  }
  if (params.end_date) {
    queryParams.end_date = params.end_date;
  }
  if (params.coin) {
    queryParams.coin = params.coin;
  }

  return await api.get("/news", {
    params: queryParams,
  });
};

export const searchPosts = async (
  query: string,
  params: ExtendedPaginationParams = INITIAL_PARAMS
): Promise<NewsFeedResponse> => {
  const queryParams: any = {
    query,
    page: params.page,
    page_size: params.page_size,
  };

  // Only include date parameters if they are provided
  if (params.start_date) {
    queryParams.start_date = params.start_date;
  }
  if (params.end_date) {
    queryParams.end_date = params.end_date;
  }
  if (params.coin) {
    queryParams.coin = params.coin;
  }

  return await api.get("/news/search", {
    params: queryParams,
  });
};

export const useGetInfinitePosts = (
  pageSize: number = DEFAULT_PAGE_SIZE,
  startDate?: string,
  endDate?: string,
  coin?: string,
  config?: QueryConfig<typeof getPosts>
) => {
  return useInfiniteQuery({
    queryKey: ["news", "list", { pageSize, startDate, endDate, coin }],
    queryFn: ({ pageParam = 1 }) =>
      getPosts({
        page: pageParam,
        page_size: pageSize,
        start_date: startDate,
        end_date: endDate,
        coin: coin,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
    ...config,
  });
};

export const useSearchInfinitePosts = (
  query: string,
  pageSize: number = DEFAULT_PAGE_SIZE,
  startDate?: string,
  endDate?: string,
  coin?: string,
  config?: QueryConfig<typeof searchPosts>
) => {
  return useInfiniteQuery({
    queryKey: ["news", "search", query, { pageSize, startDate, endDate, coin }],
    queryFn: ({ pageParam = 1 }) =>
      searchPosts(query, {
        page: pageParam,
        page_size: pageSize,
        start_date: startDate,
        end_date: endDate,
        coin: coin,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
    enabled: !!query && query.length > 0,
    ...config,
  });
};

export const useUpdatePostsCache = (
  dateFilter?: {
    startDate?: Date;
    endDate?: Date;
    startTime?: string;
    endTime?: string;
  },
  coinFilter?: string
) => {
  const queryClient = useQueryClient();

  const updatePostsCache = (news: NewsItem) => {
    // Filter websocket updates based on active coin filter
    if (coinFilter && news.coins && news.coins.length > 0) {
      const hasMatchingCoin = news.coins.some(
        (coin) => coin.symbol.toLowerCase() === coinFilter.toLowerCase()
      );
      if (!hasMatchingCoin) return;
    }

    // Filter websocket updates based on active date and time filters
    if (
      dateFilter &&
      (dateFilter.startDate ||
        dateFilter.endDate ||
        dateFilter.startTime ||
        dateFilter.endTime)
    ) {
      const itemDate = new Date(news.time);
      const itemHours = itemDate.getHours();
      const itemMinutes = itemDate.getMinutes();
      const itemTimeInMinutes = itemHours * 60 + itemMinutes;

      if (dateFilter.startDate && itemDate < dateFilter.startDate) return;
      if (dateFilter.endDate && itemDate > dateFilter.endDate) return;

      if (dateFilter.startTime) {
        const [startHours, startMinutes] = dateFilter.startTime
          .split(":")
          .map(Number);
        const startTimeInMinutes = startHours * 60 + startMinutes;
        if (itemTimeInMinutes < startTimeInMinutes) return;
      }

      if (dateFilter.endTime) {
        const [endHours, endMinutes] = dateFilter.endTime.split(":").map(Number);
        const endTimeInMinutes = endHours * 60 + endMinutes;
        if (itemTimeInMinutes > endTimeInMinutes) return;
      }
    }

    // Get all query keys from the cache to find matching ones
    const queryCache = queryClient.getQueryCache();
    const queries = queryCache.findAll();

    // Update all relevant news-feed queries
    queries.forEach((query) => {
      const queryKey = query.queryKey; // Check if this is a news-feed query
      if (
        Array.isArray(queryKey) &&
        queryKey.length >= 4 &&
        queryKey[0] === "news-feed"
      ) {
        const [, feedType, searchQuery, currentDateFilter, currentCoinFilter] =
          queryKey;

        // Only update "all" feed type queries (not bookmarked)
        if (feedType !== "all") return;

        // Only update queries without search (real-time updates shouldn't affect search results)
        if (searchQuery && searchQuery.trim() !== "") return;

        // Check if the news item matches the coin filter of this query
        if (currentCoinFilter && news.coins && news.coins.length > 0) {
          const hasMatchingCoin = news.coins.some(
            (coin) => coin.symbol.toLowerCase() === currentCoinFilter.toLowerCase()
          );
          if (!hasMatchingCoin) return;
        }

        // Check if the news item matches the date filter of this query
        if (
          currentDateFilter &&
          (currentDateFilter.startDate || currentDateFilter.endDate)
        ) {
          const itemDate = new Date(news.time);
          if (
            currentDateFilter.startDate &&
            itemDate < new Date(currentDateFilter.startDate)
          )
            return;
          if (
            currentDateFilter.endDate &&
            itemDate > new Date(currentDateFilter.endDate)
          )
            return;
        }

        // Update this specific query
        queryClient.setQueryData(queryKey, (oldData: any) => {
          if (!oldData || !oldData.pages || !oldData.pages.length) return oldData;

          const newPages = [...oldData.pages];
          const firstPage = { ...newPages[0] };

          // Check if the news item already exists to prevent duplicates
          const existingIndex = firstPage.items.findIndex(
            (item: NewsItem) => item.id === news.id
          );
          if (existingIndex === -1) {
            firstPage.items = [news, ...firstPage.items];
            newPages[0] = firstPage;

            return {
              ...oldData,
              pages: newPages,
            };
          }

          return oldData;
        });
      }
    });

    // Also update the legacy query keys for backward compatibility
    queryClient.setQueryData(
      ["news", "list", { pageSize: DEFAULT_PAGE_SIZE, coin: coinFilter }],
      (oldData: any) => {
        if (!oldData || !oldData.pages || !oldData.pages.length) return oldData;

        const newPages = [...oldData.pages];
        const firstPage = { ...newPages[0] };

        const existingIndex = firstPage.items.findIndex(
          (item: NewsItem) => item.id === news.id
        );
        if (existingIndex === -1) {
          firstPage.items = [news, ...firstPage.items];
          newPages[0] = firstPage;

          return {
            ...oldData,
            pages: newPages,
          };
        }

        return oldData;
      }
    );
  };

  return updatePostsCache;
};

import { useQuery, useQueryClient, useInfiniteQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";
import { PaginationParams } from "@/types/api";

import { NewsItem, NewsFeedResponse } from "../types";

const DEFAULT_PAGE_SIZE = 20;

interface ExtendedPaginationParams extends PaginationParams {
  start_date?: string;
  end_date?: string;
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

  return await api.get("/news/search", {
    params: queryParams,
  });
};

export const useGetInfinitePosts = (
  pageSize: number = DEFAULT_PAGE_SIZE,
  startDate?: string,
  endDate?: string,
  config?: QueryConfig<typeof getPosts>
) => {
  return useInfiniteQuery({
    queryKey: ["news", "list", { pageSize, startDate, endDate }],
    queryFn: ({ pageParam = 1 }) =>
      getPosts({
        page: pageParam,
        page_size: pageSize,
        start_date: startDate,
        end_date: endDate,
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
  config?: QueryConfig<typeof searchPosts>
) => {
  return useInfiniteQuery({
    queryKey: ["news", "search", query, { pageSize, startDate, endDate }],
    queryFn: ({ pageParam = 1 }) =>
      searchPosts(query, {
        page: pageParam,
        page_size: pageSize,
        start_date: startDate,
        end_date: endDate,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
    enabled: !!query && query.length > 0,
    ...config,
  });
};

export const useUpdatePostsCache = (dateFilter?: {
  startDate?: Date;
  endDate?: Date;
  startTime?: string;
  endTime?: string;
}) => {
  const queryClient = useQueryClient();

  const updatePostsCache = (news: NewsItem) => {
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

    // Update query cache for the default params
    queryClient.setQueryData(
      ["news", "list", { pageSize: DEFAULT_PAGE_SIZE }],
      (oldData: any) => {
        if (!oldData || !oldData.pages || !oldData.pages.length) return oldData;

        const newPages = [...oldData.pages];
        const firstPage = { ...newPages[0] };

        firstPage.items = [news, ...firstPage.items];
        newPages[0] = firstPage;

        return {
          ...oldData,
          pages: newPages,
        };
      }
    );

    // Also update cache for queries with date filters
    queryClient.setQueryData(
      ["news-feed", "all", "", dateFilter],
      (oldData: any) => {
        if (!oldData || !oldData.pages || !oldData.pages.length) return oldData;

        const newPages = [...oldData.pages];
        const firstPage = { ...newPages[0] };

        firstPage.items = [news, ...firstPage.items];
        newPages[0] = firstPage;

        return {
          ...oldData,
          pages: newPages,
        };
      }
    );
  };

  return updatePostsCache;
};

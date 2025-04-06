import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";
import { PaginationParams } from "@/types/api";

import { NewsItem, NewsFeedResponse } from "../types";

const DEFAULT_PAGE_SIZE = 20;

export const getNews = async (
  params: PaginationParams = { page: 1, page_size: DEFAULT_PAGE_SIZE }
): Promise<NewsFeedResponse> => {
  return api.get<NewsFeedResponse>("/news/feed", {
    params: {
      page: params.page,
      page_size: params.page_size,
    },
  });
};

export const useGetNews = (
  params: PaginationParams = { page: 1, page_size: DEFAULT_PAGE_SIZE },
  config?: QueryConfig<typeof getNews>
) => {
  return useQuery({
    queryKey: ["news", "feed", params],
    queryFn: () => getNews(params),
    ...config,
  });
};

export const useUpdateNewsCache = () => {
  const queryClient = useQueryClient();

  const updateNewsCache = (news: NewsItem) => {
    const defaultParams = { page: 1, page_size: DEFAULT_PAGE_SIZE };

    // Update query cache for the default params
    queryClient.setQueryData(
      ["news", "feed", defaultParams],
      (oldData: NewsFeedResponse | undefined) => {
        if (!oldData) return oldData;

        return {
          ...oldData,
          items: [news, ...(oldData.items || [])],
        };
      }
    );
  };

  return updateNewsCache;
};

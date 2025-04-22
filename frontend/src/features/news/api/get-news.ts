import { useQuery, useQueryClient, useInfiniteQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";
import { PaginationParams } from "@/types/api";

import { NewsItem, NewsFeedResponse } from "../types";

const DEFAULT_PAGE_SIZE = 20;
const INITIAL_PARAMS = {
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
};

export const getPosts = async (
  params: PaginationParams = INITIAL_PARAMS
): Promise<NewsFeedResponse> => {
  return await api.get("/news", {
    params: {
      page: params.page,
      page_size: params.page_size,
    },
  });
};

export const searchPosts = async (
  query: string,
  params: PaginationParams = INITIAL_PARAMS
): Promise<NewsFeedResponse> => {
  return await api.get("/news/search", {
    params: {
      query,
      page: params.page,
      page_size: params.page_size,
    },
  });
};

export const useGetInfinitePosts = (
  pageSize: number = DEFAULT_PAGE_SIZE,
  config?: QueryConfig<typeof getPosts>
) => {
  return useInfiniteQuery({
    queryKey: ["news", "list", { pageSize }],
    queryFn: ({ pageParam = 1 }) =>
      getPosts({ page: pageParam, page_size: pageSize }),
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
    ...config,
  });
};

export const useSearchInfinitePosts = (
  query: string,
  pageSize: number = DEFAULT_PAGE_SIZE,
  config?: QueryConfig<typeof searchPosts>
) => {
  return useInfiniteQuery({
    queryKey: ["news", "search", query, { pageSize }],
    queryFn: ({ pageParam = 1 }) =>
      searchPosts(query, { page: pageParam, page_size: pageSize }),
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
    enabled: !!query && query.length > 0,
    ...config,
  });
};

export const useUpdatePostsCache = () => {
  const queryClient = useQueryClient();

  const updatePostsCache = (news: NewsItem) => {
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
  };

  return updatePostsCache;
};

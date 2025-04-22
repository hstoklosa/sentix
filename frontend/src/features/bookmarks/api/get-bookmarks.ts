import { useInfiniteQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

import { BookmarkedNewsResponse } from "../types";
import { MutationConfig, QueryConfig } from "@/lib/react-query";

export const getBookmarkedPosts = async ({ pageParam = 1 }) => {
  // The api client already returns response.data due to interceptors
  const data = await api.get<never, BookmarkedNewsResponse>("/bookmarks", {
    params: {
      page: pageParam,
      limit: 20,
    },
  });
  return data;
};

export const useGetInfiniteBookmarkedPosts = (
  config?: QueryConfig<typeof useInfiniteQuery>
) => {
  return useInfiniteQuery({
    queryKey: ["bookmarkedPosts"],
    queryFn: ({ pageParam }) => getBookmarkedPosts({ pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.page < lastPage.total_pages) {
        return lastPage.page + 1;
      }
      return undefined;
    },
    ...config,
  });
};

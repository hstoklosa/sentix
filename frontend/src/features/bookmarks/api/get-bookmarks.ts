import { useInfiniteQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

import { BookmarkedNewsResponse } from "../types";
import { QueryConfig } from "@/lib/react-query";

interface BookmarkParams {
  pageParam?: number;
  query?: string;
  start_date?: string;
  end_date?: string;
  coin?: string;
}

export const getBookmarkedPosts = async ({
  pageParam = 1,
  query,
  start_date,
  end_date,
  coin,
}: BookmarkParams) => {
  const queryParams: any = {
    page: pageParam,
    page_size: 20,
  };

  // Only include parameters if they are provided
  if (query) {
    queryParams.query = query;
  }
  if (start_date) {
    queryParams.start_date = start_date;
  }
  if (end_date) {
    queryParams.end_date = end_date;
  }
  if (coin) {
    queryParams.coin = coin;
  }

  // The api client already returns response.data due to interceptors
  const data = await api.get<never, BookmarkedNewsResponse>("/bookmarks", {
    params: queryParams,
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

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { api } from "@/lib/api-client";
import { BookmarkCreate, BookmarkResponse } from "../types";
import { NewsItem } from "@/features/news/types";

const createBookmark = async (data: BookmarkCreate): Promise<BookmarkResponse> => {
  return api.post("/bookmarks", data);
};

export const useCreateBookmark = () => {
  const queryClient = useQueryClient();

  return useMutation<BookmarkResponse, AxiosError, BookmarkCreate>({
    mutationFn: createBookmark,
    onSuccess: (_, variables) => {
      // Update the news list cache (infinite query)
      queryClient.setQueriesData({ queryKey: ["news", "list"] }, (oldData: any) => {
        if (!oldData || !oldData.pages) return oldData;

        // Update infinite query cache
        return {
          ...oldData,
          pages: oldData.pages.map((page: any) => ({
            ...page,
            items: page.items.map((item: NewsItem) =>
              item.id === variables.news_item_id
                ? { ...item, is_bookmarked: true }
                : item
            ),
          })),
        };
      });

      // Also update the individual post detail cache if it exists
      queryClient.setQueryData(
        ["news", "post", variables.news_item_id],
        (oldData: NewsItem | undefined) => {
          if (!oldData) return oldData;
          return { ...oldData, is_bookmarked: true };
        }
      );
    },
  });
};

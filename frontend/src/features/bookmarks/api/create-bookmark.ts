import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { api } from "@/lib/api-client";
import { MutationConfig } from "@/lib/react-query";
import { NewsItem } from "@/features/news/types";

import { BookmarkCreate, BookmarkResponse } from "../types";

const createBookmark = async (data: BookmarkCreate): Promise<BookmarkResponse> => {
  return api.post("/bookmarks", data);
};

export const useCreateBookmark = ({
  onSuccess,
  onError,
}: Omit<MutationConfig<typeof createBookmark>, "mutationFn">) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createBookmark,
    onSuccess: (data, variables, context) => {
      // Update the news feed cache (infinite query)
      queryClient.setQueriesData({ queryKey: ["news-feed"] }, (oldData: any) => {
        if (!oldData || !oldData.pages) return oldData;

        // Update infinite query cache
        return {
          ...oldData,
          pages: oldData.pages.map((page: any) => ({
            ...page,
            items: page.items.map((item: NewsItem) =>
              item.id === variables.post_id
                ? { ...item, is_bookmarked: true, bookmark_id: data.id }
                : item
            ),
          })),
        };
      });

      // Also update the individual post detail cache if it exists
      queryClient.setQueryData(
        ["news", "post", variables.post_id],
        (oldData: NewsItem | undefined) => {
          if (!oldData) return oldData;
          return { ...oldData, is_bookmarked: true, bookmark_id: data.id };
        }
      );

      // Invalidate the bookmarkedPosts query to refresh the list when a new item is bookmarked
      queryClient.invalidateQueries({ queryKey: ["bookmarkedPosts"] });

      onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      onError?.(error as AxiosError, variables, context);
    },
  });
};

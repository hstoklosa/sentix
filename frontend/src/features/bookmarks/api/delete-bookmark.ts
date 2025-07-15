import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { api } from "@/lib/api-client";
import { MutationConfig } from "@/lib/react-query";
import { NewsItem } from "@/features/news/types";

const deleteBookmark = async (postId: number): Promise<void> => {
  return api.delete(`/bookmarks/${postId}`);
};

export const useDeleteBookmark = ({
  onSuccess,
  onError,
}: Omit<MutationConfig<typeof deleteBookmark>, "mutationFn">) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteBookmark,
    onSuccess: (data, postId, context) => {
      // Update the news feed cache (infinite query)
      queryClient.setQueriesData({ queryKey: ["news-feed"] }, (oldData: any) => {
        if (!oldData || !oldData.pages) return oldData;

        // Update infinite query cache
        return {
          ...oldData,
          pages: oldData.pages.map((page: any) => ({
            ...page,
            items: page.items.map((item: NewsItem) =>
              item.id === postId
                ? {
                    ...item,
                    is_bookmarked: false,
                    bookmark_id: undefined,
                  }
                : item
            ),
          })),
        };
      });

      // Also update the individual post detail cache if it exists
      queryClient.setQueryData(
        ["news", "post", postId],
        (oldData: NewsItem | undefined) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            is_bookmarked: false,
            bookmark_id: undefined,
          };
        }
      );

      // Invalidate the bookmarkedPosts query to refresh the list
      // This is needed to remove the item from the bookmarked view
      queryClient.invalidateQueries({ queryKey: ["bookmarkedPosts"] });

      onSuccess?.(data, postId, context);
    },
    onError: (error, postId, context) => {
      onError?.(error as AxiosError, postId, context);
    },
  });
};

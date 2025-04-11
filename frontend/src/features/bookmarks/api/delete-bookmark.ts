import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { api } from "@/lib/api-client";
import { NewsItem } from "@/features/news/types";

const deleteBookmark = async (newsItemId: number): Promise<void> => {
  return api.delete(`/bookmarks/${newsItemId}`);
};

export const useDeleteBookmark = () => {
  const queryClient = useQueryClient();

  return useMutation<void, AxiosError, number>({
    mutationFn: deleteBookmark,
    onSuccess: (_, newsItemId) => {
      // Update the news list cache (infinite query)
      queryClient.setQueriesData({ queryKey: ["news", "list"] }, (oldData: any) => {
        if (!oldData || !oldData.pages) return oldData;

        // Update infinite query cache
        return {
          ...oldData,
          pages: oldData.pages.map((page: any) => ({
            ...page,
            items: page.items.map((item: NewsItem) =>
              item.id === newsItemId ? { ...item, is_bookmarked: false } : item
            ),
          })),
        };
      });

      // Also update the individual post detail cache if it exists
      queryClient.setQueryData(
        ["news", "post", newsItemId],
        (oldData: NewsItem | undefined) => {
          if (!oldData) return oldData;
          return { ...oldData, is_bookmarked: false };
        }
      );
    },
  });
};

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { api } from "@/lib/api-client";
import { MutationConfig } from "@/lib/react-query";
import { NewsItem } from "@/features/news/types";

const deleteBookmark = async (newsItemId: number): Promise<void> => {
  return api.delete(`/bookmarks/${newsItemId}`);
};

export const useDeleteBookmark = ({
  onSuccess,
  onError,
}: Omit<MutationConfig<typeof deleteBookmark>, "mutationFn">) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteBookmark,
    onSuccess: (data, newsItemId, context) => {
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

      onSuccess?.(data, newsItemId, context);
    },
    onError: (error, newsItemId, context) => {
      onError?.(error as AxiosError, newsItemId, context);
    },
  });
};

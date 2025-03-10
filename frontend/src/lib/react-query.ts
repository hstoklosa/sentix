import { DefaultOptions, QueryClient } from "@tanstack/react-query";

export const queryConfig = {
  queries: {
    refetchOnWindowFocus: false,
    retry: false,
    staleTime: 1000 * 60,
  },
} satisfies DefaultOptions;

export const createQueryClient = () =>
  new QueryClient({
    defaultOptions: queryConfig,
  });

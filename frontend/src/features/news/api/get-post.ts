import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { QueryConfig } from "@/lib/react-query";

import { NewsItem } from "../types";

export const getPost = async (id: number): Promise<NewsItem> => {
  // The api client handles response.data automatically in interceptors
  return api.get(`/news/${id}`);
};

export const useGetPost = (id: number, config?: QueryConfig<typeof getPost>) => {
  return useQuery({
    queryKey: ["news", "post", id],
    queryFn: () => getPost(id),
    ...config,
  });
};

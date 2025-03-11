import type { QueryClient } from "@tanstack/react-query";
import type { AuthState } from "@/hooks/use-auth";

export type RouterContext = {
  auth: AuthState;
  queryClient: QueryClient;
};

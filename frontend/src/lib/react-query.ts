import {
  DefaultOptions,
  QueryClient,
  UseMutationOptions,
} from "@tanstack/react-query";
import { AxiosError } from "axios";

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

// REF: https://github.com/alan2207/bulletproof-react/blob/master/apps/react-vite/src/lib/react-query.ts
export type ApiFnReturnType<FnType extends (...args: any) => Promise<any>> =
  Awaited<ReturnType<FnType>>;

export type QueryConfig<T extends (...args: any[]) => any> = Omit<
  ReturnType<T>,
  "queryKey" | "queryFn"
>;

export type MutationConfig<MutationFnType extends (...args: any) => Promise<any>> =
  UseMutationOptions<
    ApiFnReturnType<MutationFnType>,
    AxiosError,
    Parameters<MutationFnType>[0]
  >;

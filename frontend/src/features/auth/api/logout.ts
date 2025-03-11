import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { MutationConfig } from "@/lib/react-query";
import { useLocalStorage } from "@/hooks/use-local-storage";

import { userQueryKeys } from "./query-keys";

const logout = (): Promise<void> => {
  return api.post("/auth/logout");
};

export const useLogout = ({
  onSuccess,
  ...rest
}: Omit<MutationConfig<typeof logout>, "mutationFn">) => {
  const queryClient = useQueryClient();
  const [_, setAuthToken] = useLocalStorage<string | null>("access_token", null);

  return useMutation({
    mutationFn: logout,
    onSuccess: (...args) => {
      setAuthToken(null);
      queryClient.setQueryData(userQueryKeys.all, () => null);
      onSuccess && onSuccess(...args);
    },
    ...rest,
  });
};

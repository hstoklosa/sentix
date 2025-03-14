import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { MutationConfig } from "@/lib/react-query";
import { useLocalStorage } from "@/hooks/use-local-storage";
import { AuthResponse } from "@/types/api";

import { userQueryKeys } from "./query-keys";
import { LoginFormValues } from "../types";

const login = async (data: LoginFormValues): Promise<AuthResponse> => {
  return api.post("/auth/login", data);
};

export const useLogin = ({
  onSuccess,
  ...rest
}: Omit<MutationConfig<typeof login>, "mutationFn">) => {
  const queryClient = useQueryClient();
  const [_, setAuthToken] = useLocalStorage<string | null>("access_token", null);

  return useMutation({
    mutationFn: login,
    onSuccess: (data, ...args) => {
      setAuthToken(data.token.access_token);
      queryClient.setQueryData(userQueryKeys.all, () => data.user);
      onSuccess && onSuccess(data, ...args);
    },
    ...rest,
  });
};

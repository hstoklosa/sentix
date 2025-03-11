import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { MutationConfig } from "@/lib/react-query";
import { AuthResponse } from "@/types/api";
import { useLocalStorage } from "@/hooks/use-local-storage";

import { userQueryKeys } from "./query-keys";
import { RegisterFormValues } from "../types";

const register = async (data: RegisterFormValues): Promise<AuthResponse> => {
  return api.post("/auth/register", data);
};

export const useRegister = ({
  onSuccess,
  ...rest
}: Omit<MutationConfig<typeof register>, "mutationFn">) => {
  const queryClient = useQueryClient();
  const [_, setAuthToken] = useLocalStorage<string | null>("access_token", null);

  return useMutation({
    mutationFn: register,
    onSuccess: (data, ...args) => {
      setAuthToken(data.token.access_token);
      queryClient.setQueryData(userQueryKeys.all, () => data.user);
      onSuccess && onSuccess(data, ...args);
    },
    ...rest,
  });
};

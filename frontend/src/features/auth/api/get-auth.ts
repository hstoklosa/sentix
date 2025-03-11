import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api-client";
import { User } from "@/types/api";

import { userQueryKeys } from "./query-keys";

const getAuth = async (): Promise<User> => {
  return api.get("/auth/me");
};

export const useAuthQuery = () => {
  return useQuery({
    queryKey: userQueryKeys.all,
    queryFn: getAuth,
  });
};

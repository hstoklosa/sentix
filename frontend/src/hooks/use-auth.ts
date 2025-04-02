import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
// import { useRouter } from "@tanstack/react-router";

import { router } from "@/app/router";

import { useAuthQuery } from "@/features/auth/api/get-auth";
import { User } from "@/types/api";

export type AuthState =
  | { user: null; status: "PENDING" }
  | { user: null; status: "UNAUTHENTICATED" }
  | { user: User; status: "AUTHENTICATED" };

const useAuth = (): AuthState => {
  const queryClient = useQueryClient();
  const authQuery = useAuthQuery();
  // const router = useRouter();

  useEffect(() => {
    router.invalidate();
  }, [authQuery.data]);

  useEffect(() => {
    if (authQuery.error === null) return;
    queryClient.setQueryData(["auth"], null);
  }, [authQuery.error, queryClient]);

  switch (true) {
    case !!authQuery.data:
      return { user: authQuery.data, status: "AUTHENTICATED" };
    case authQuery.isPending:
      return { user: null, status: "PENDING" };
    default:
      return { user: null, status: "UNAUTHENTICATED" };
  }
};

export default useAuth;

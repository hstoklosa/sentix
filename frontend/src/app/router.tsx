import { RouterProvider, createRouter } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";

import useAuth, { type AuthState } from "@/hooks/use-auth";

import { routeTree } from "./route-tree.gen";

// Initialise a router instance
export const router = createRouter({
  routeTree,
  context: {
    queryClient: undefined!,
    auth: null as unknown as AuthState,
  },
  defaultPreload: "intent",
  // Since we're using React Query, we don't want loader calls to ever be stale
  // Ensure that the loader is always called when the route is preloaded or visited
  defaultPreloadStaleTime: 0,
});

// Register the instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const AppRouter = () => {
  const queryClient = useQueryClient();
  const auth = useAuth();

  return (
    <RouterProvider
      router={router}
      context={{ queryClient, auth }}
    />
  );
};

export default AppRouter;

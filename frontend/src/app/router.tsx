import { RouterProvider, createRouter } from "@tanstack/react-router";
import { routeTree } from "@/app/routeTree.gen";

// Initialise router instance
const router = createRouter({
  routeTree,
  defaultPreload: "intent",
});

// Register router instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const AppRouter = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;

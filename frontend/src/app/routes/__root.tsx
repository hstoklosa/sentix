import { Outlet, createRootRouteWithContext } from "@tanstack/react-router";
import { RouterContext } from "@/types/router";

const Root = () => {
  return (
    <div className="h-screen w-full mx-auto px-4">
      <Outlet />
    </div>
  );
};

export const Route = createRootRouteWithContext<RouterContext>()({
  component: Root,
});

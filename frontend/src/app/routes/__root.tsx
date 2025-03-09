import { Outlet, createRootRoute } from "@tanstack/react-router";

const Root = () => {
  return (
    <div className="h-screen w-full mx-auto px-4">
      <Outlet />
    </div>
  );
};

export const Route = createRootRoute({
  component: Root,
});

import { Outlet, createRootRouteWithContext } from "@tanstack/react-router";

import { RootLayout } from "@/components/layout";
import { RouterContext } from "@/types/router";

const Root = () => {
  return (
    <RootLayout>
      <Outlet />
    </RootLayout>
  );
};

export const Route = createRootRouteWithContext<RouterContext>()({
  component: Root,
});

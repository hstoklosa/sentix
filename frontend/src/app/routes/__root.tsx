import {
  Outlet,
  createRootRouteWithContext,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";

import { RootLayout } from "@/components/layout";
import { NotFound } from "@/components/error";
import { RouterContext } from "@/types/router";

const Root = () => {
  return (
    <RootLayout>
      <HeadContent />
      <Outlet />
      <Scripts />

      {/* {import.meta.env.DEV && ()} */}
      <TanStackRouterDevtools
        position="bottom-right"
        initialIsOpen={false}
      />
    </RootLayout>
  );
};

export const Route = createRootRouteWithContext<RouterContext>()({
  component: Root,
  notFoundComponent: NotFound,
  head: () => ({
    meta: [{ title: "Sentix" }],
    links: [{ rel: "icon", href: "/favicon-bg.png" }],
  }),
});

import {
  Outlet,
  createRootRouteWithContext,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";

import { RootLayout } from "@/components/layout";
import { NotFound } from "@/components/error";
import { Spinner } from "@/components/ui";

import { RouterContext } from "@/types/router";
import useAuth from "@/hooks/use-auth";

const Root = () => {
  const auth = useAuth();

  if (auth.status === "PENDING") {
    return (
      <Spinner
        size="lg"
        fullScreen
      />
    );
  }

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

import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";

import { AppLayout } from "@/components/layout";

import { LiveNewsProvider } from "@/features/news/hooks";
import { BinanceWebSocketProviderWrapper } from "@/features/coins/context";

const DashboardLayout = () => {
  return (
    <LiveNewsProvider>
      <BinanceWebSocketProviderWrapper>
        <AppLayout>
          <Outlet />
        </AppLayout>
      </BinanceWebSocketProviderWrapper>
    </LiveNewsProvider>
  );
};

export const Route = createFileRoute("/_app")({
  beforeLoad: ({ context }) => {
    if (context.auth.status === "UNAUTHENTICATED") {
      throw redirect({
        to: "/login",
        search: { redirect: location.href },
      });
    }
  },
  component: DashboardLayout,
});

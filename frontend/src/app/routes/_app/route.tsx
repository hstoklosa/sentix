import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout";
import { WebSocketProviderWrapper } from "@/features/news/context";
import { BinanceWebSocketProviderWrapper } from "@/features/coins/context";

const DashboardLayout = () => {
  return (
    <WebSocketProviderWrapper>
      <BinanceWebSocketProviderWrapper>
        <AppLayout>
          <Outlet />
        </AppLayout>
      </BinanceWebSocketProviderWrapper>
    </WebSocketProviderWrapper>
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

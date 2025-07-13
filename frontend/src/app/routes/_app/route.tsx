import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";

import { AppLayout } from "@/components/layout";
import { DisclaimerAlert } from "@/components/disclaimer-alert";

import { LiveNewsProvider } from "@/features/news/context";
import { BinanceWebSocketProviderWrapper } from "@/features/coins/context";
import { useUpdatePostsCache } from "@/features/news/api/get-news";

const DashboardLayout = () => {
  // For now, we'll use a basic updatePostsCache without date filtering
  // The actual filtering will be handled in the individual news list components
  const updatePostsCache = useUpdatePostsCache();

  return (
    <LiveNewsProvider onMessage={updatePostsCache}>
      <BinanceWebSocketProviderWrapper>
        <AppLayout>
          <DisclaimerAlert />
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

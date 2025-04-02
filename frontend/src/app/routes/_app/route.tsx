import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout";

const DashboardLayout = () => {
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
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

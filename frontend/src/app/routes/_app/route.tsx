import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { Spinner } from "@/components/ui";

const DashboardLayout = () => {
  const { auth } = Route.useRouteContext();

  if (auth.status === "PENDING") {
    return (
      <Spinner
        size="lg"
        fullScreen
      />
    );
  }

  return (
    <div>
      <Outlet />
    </div>
  );
};

export const Route = createFileRoute("/_app")({
  beforeLoad: ({ context }) => {
    // Only redirect if explicitly UNAUTHENTICATED (proceed to component if PENDING)
    if (context.auth.status === "UNAUTHENTICATED") {
      throw redirect({
        to: "/login",
        search: { redirect: location.href },
      });
    }
  },
  component: DashboardLayout,
});

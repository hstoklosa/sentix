import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";

const DashboardLayout = () => {
  return (
    <div>
      <Outlet />
    </div>
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

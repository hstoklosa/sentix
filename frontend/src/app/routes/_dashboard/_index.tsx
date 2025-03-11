import { createFileRoute, Outlet } from "@tanstack/react-router";

const DashboardLayout = () => {
  return (
    <div>
      <h1>Dashboard</h1>
      <Outlet />
    </div>
  );
};

export const Route = createFileRoute("/_dashboard/_index")({
  component: DashboardLayout,
});

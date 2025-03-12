import { createFileRoute, useRouter } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { useLogout } from "@/features/auth/api/logout";

function RouteComponent() {
  const router = useRouter();
  const navigate = Route.useNavigate();
  const logoutMutation = useLogout({
    onSuccess: () => {
      router.invalidate().finally(() => {
        navigate({ to: "/" });
      });
    },
  });

  return (
    <div>
      <h1>Dashboard</h1>
      <Button onClick={() => logoutMutation.mutate(undefined)}>Logout</Button>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard")({
  component: RouteComponent,
  head: () => ({
    meta: [{ title: "Dashboard | Sentix" }],
  }),
});

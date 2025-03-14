import { createFileRoute, useRouter } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";

import { useLogout } from "@/features/auth/api/logout";
import { NewsList } from "@/features/news";

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
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
        <Button onClick={() => logoutMutation.mutate(undefined)}>Logout</Button>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* News section */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <NewsList maxItems={10} />
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard")({
  component: RouteComponent,
  head: () => ({
    meta: [{ title: "Dashboard | Sentix" }],
  }),
});

import { createFileRoute, Outlet } from "@tanstack/react-router";

import Logo from "@/components/logo";
import { NewsList } from "@/features/news/components";

function RouteComponent() {
  return (
    <div className="grid grid-cols-[repeat(3,1fr)] grid-rows-[repeat(4,1fr)] gap-x-2 gap-y-2 h-[calc(100vh-4.5rem)] overflow-hidden">
      <div className="row-start-1 row-end-5 col-start-1 col-end-2 flex flex-col border-1 border-border rounded-md bg-card">
        <NewsList />
      </div>

      <div className="row-start-1 row-end-3 col-start-2 col-end-3 h-full flex flex-col border-1 border-border rounded-md bg-card overflow-hidden">
        <div className="h-full overflow-y-auto">
          <Outlet />
        </div>
      </div>

      <div className="row-start-3 row-end-5 col-start-2 col-end-3 h-full flex flex-col justify-center items-center border-1 border-border rounded-md bg-card">
        <Logo className="size-16" />
      </div>

      <div className="row-start-1 row-end-2 col-start-3 col-end-4 h-full flex flex-col justify-center items-center border-1 border-border rounded-md bg-card">
        <Logo className="size-16" />
      </div>

      <div className="row-start-2 row-end-5 col-start-3 col-end-4 h-full flex flex-col justify-center items-center border-1 border-border rounded-md bg-card">
        <Logo className="size-16" />
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

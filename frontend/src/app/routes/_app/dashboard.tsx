import { createFileRoute } from "@tanstack/react-router";

import { NewsList } from "@/features/news/components";

function RouteComponent() {
  return (
    <div className="grid grid-cols-[repeat(3,1fr)] grid-rows-[repeat(3,1fr)] gap-x-2 gap-y-2 h-[calc(100vh-4.5rem)] overflow-hidden">
      <div className="row-start-1 row-end-4 col-start-1 col-end-2 flex flex-col border-1 border-border rounded-md">
        <NewsList />
      </div>

      <div className="row-start-1 row-end-2 col-start-2 col-end-4 flex flex-col border-1 border-border rounded-md">
        2
      </div>

      <div className="row-start-2 row-end-4 col-start-2 col-end-3 flex flex-col border-1 border-border rounded-md">
        3
      </div>

      <div className="row-start-2 row-end-4 col-start-3 col-end-4 flex flex-col border-1 border-border rounded-md">
        4
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

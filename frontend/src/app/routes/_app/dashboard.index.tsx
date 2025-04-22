import { createFileRoute } from "@tanstack/react-router";

function DashboardIndexComponent() {
  return (
    <div className="flex flex-col h-full">
      <div className="py-2 px-3 flex items-center border-b border-border h-[40px]">
        <h2 className="text-lg font-semibold">Dashboard</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="text-muted-foreground text-sm">
          Select a news item from the list to view details.
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard/")({
  component: DashboardIndexComponent,
});

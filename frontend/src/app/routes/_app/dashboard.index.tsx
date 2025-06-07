import { createFileRoute } from "@tanstack/react-router";
import { TrendingCoinsChart } from "@/features/trending";

function DashboardIndexComponent() {
  return (
    <div className="flex flex-col h-full">
      <div className="py-2 px-3 flex items-center border-b border-border h-[45px]">
        <h2 className="text-md font-semibold">Top Mentioned Coins</h2>
      </div>
      <div className="flex-1 overflow-auto">
        <TrendingCoinsChart
          limit={20}
          className="w-full"
        />
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard/")({
  component: DashboardIndexComponent,
});

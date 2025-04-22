import { createFileRoute, Outlet, useRouterState } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

import { NewsList } from "@/features/news/components";
import { MarketStatsPanel } from "@/features/market/components";
import { WatchlistList } from "@/features/watchlist/components";

type DashboardContainerProps = {
  rows?: number;
  columns?: number;
  children: React.ReactNode;
};

const DashboardContainer = ({
  rows = 4,
  columns = 3,
  children,
}: DashboardContainerProps) => {
  return (
    <div
      className="grid gap-2 h-[calc(100vh-4.5rem)] overflow-hidden"
      style={{
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gridTemplateRows: `repeat(${rows}, 1fr)`,
      }}
    >
      {children}
    </div>
  );
};

type PanelPosition = {
  rowStart: number;
  rowEnd?: number;
  colStart: number;
  colEnd?: number;
};

export const DashboardPanel = ({
  position,
  className,
  children,
}: {
  position: PanelPosition;
  className?: string;
  children: React.ReactNode;
}) => {
  const { rowStart, rowEnd, colStart, colEnd } = position;

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-card border-1 border-border rounded-md",
        className
      )}
      style={{
        gridRowStart: rowStart,
        gridRowEnd: rowEnd,
        gridColumnStart: colStart,
        gridColumnEnd: colEnd,
      }}
    >
      {children}
    </div>
  );
};

function RouteComponent() {
  const { location } = useRouterState();
  const isViewingPost =
    location.pathname.includes("/dashboard/") &&
    !location.pathname.endsWith("/dashboard/");

  return (
    <DashboardContainer
      rows={5}
      columns={3}
    >
      <DashboardPanel position={{ rowStart: 1, rowEnd: 6, colStart: 1, colEnd: 2 }}>
        <NewsList />
      </DashboardPanel>

      <DashboardPanel
        position={{ rowStart: 1, rowEnd: 6, colStart: 2, colEnd: 3 }}
        className={isViewingPost ? "p-0 bg-transparent border-0" : undefined}
      >
        <Outlet />
      </DashboardPanel>

      <DashboardPanel position={{ rowStart: 1, rowEnd: 2, colStart: 3, colEnd: 4 }}>
        <MarketStatsPanel />
      </DashboardPanel>

      <DashboardPanel position={{ rowStart: 2, rowEnd: 6, colStart: 3, colEnd: 4 }}>
        <WatchlistList />
      </DashboardPanel>
    </DashboardContainer>
  );
}

export const Route = createFileRoute("/_app/dashboard")({
  component: RouteComponent,
  head: () => ({
    meta: [{ title: "Dashboard | Sentix" }],
  }),
});

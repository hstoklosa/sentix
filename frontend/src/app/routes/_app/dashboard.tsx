import { createFileRoute, Outlet } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { NewsList } from "@/features/news/components";

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
      className={`grid grid-cols-[repeat(${columns},1fr)] grid-rows-[repeat(${rows},1fr)] gap-x-2 gap-y-2 h-[calc(100vh-4.5rem)] overflow-hidden`}
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

const DashboardPanel = ({
  position,
  className,
  children,
}: {
  position: PanelPosition;
  className?: string;
  children: React.ReactNode;
}) => {
  const { rowStart, rowEnd, colStart, colEnd } = position;
  const positionClasses = `row-start-${rowStart} ${rowEnd ? `row-end-${rowEnd}` : ""} col-start-${colStart} ${colEnd ? `col-end-${colEnd}` : ""}`;

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-card border-1 border-border rounded-md",
        positionClasses,
        className
      )}
    >
      {children}
    </div>
  );
};

function RouteComponent() {
  return (
    <DashboardContainer
      rows={4}
      columns={3}
    >
      <DashboardPanel position={{ rowStart: 1, rowEnd: 5, colStart: 1, colEnd: 2 }}>
        <NewsList />
      </DashboardPanel>
      <DashboardPanel position={{ rowStart: 1, rowEnd: 3, colStart: 2, colEnd: 3 }}>
        <Outlet />
      </DashboardPanel>
      <DashboardPanel position={{ rowStart: 3, rowEnd: 5, colStart: 2, colEnd: 3 }}>
        Charts
      </DashboardPanel>
      <DashboardPanel position={{ rowStart: 1, rowEnd: 2, colStart: 3, colEnd: 4 }}>
        Market stats
      </DashboardPanel>
      <DashboardPanel position={{ rowStart: 2, rowEnd: 5, colStart: 3, colEnd: 4 }}>
        Screeners
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

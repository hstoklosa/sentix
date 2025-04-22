import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { useGetTrendingCoins } from "../api/get-trending-coins";
import { formatCurrencyAmount } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface TrendingCoinsChartProps {
  limit?: number;
  className?: string;
}

export const TrendingCoinsChart = ({
  limit = 10,
  className,
}: TrendingCoinsChartProps) => {
  const { data, isLoading, error } = useGetTrendingCoins({
    page: 1,
    page_size: limit,
  });

  const chartData = useMemo(() => {
    if (!data?.items) return [];

    // Convert the data to chart format and sort by mention count (descending)
    return [...data.items]
      .sort((a, b) => b.mention_count - a.mention_count)
      .map((coin) => ({
        name: coin.symbol.toUpperCase(),
        value: coin.mention_count,
        fullName: coin.name || coin.symbol.toUpperCase(),
        sentimentStats: coin.sentiment_stats,
        icon: coin.image_url,
      }));
  }, [data]);

  const chartConfig = useMemo(
    () => ({
      coin: {
        theme: {
          light: "#10B981",
          dark: "#10B981",
        },
      },
    }),
    []
  );

  // Custom tick renderer for the X-axis with icons next to symbol names
  const CustomXAxisTick = (props: any) => {
    const { x, y, payload } = props;
    const coin = chartData.find((item) => item.name === payload.value);

    return (
      <g transform={`translate(${x},${y})`}>
        <foreignObject
          x="-30"
          y="3"
          width="60"
          height="20"
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              height: "100%",
              fontSize: "13px",
              fontWeight: 500,
            }}
          >
            {coin?.icon && (
              <img
                src={coin.icon}
                alt={payload.value}
                style={{
                  width: "14px",
                  height: "14px",
                  marginRight: "4px",
                }}
              />
            )}
            <span>{payload.value}</span>
          </div>
        </foreignObject>
      </g>
    );
  };

  if (isLoading) {
    return <Skeleton className="h-full w-full" />;
  }

  if (error || !data) {
    return <div>Error loading trending coins data</div>;
  }

  return (
    <div className={`h-full ${className}`}>
      <ChartContainer
        config={chartConfig}
        className="h-full"
      >
        <BarChart
          data={chartData}
          layout="horizontal"
          margin={{ top: 20, right: 40, left: 10, bottom: 20 }}
          barCategoryGap={3}
          maxBarSize={undefined}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            horizontal={true}
            vertical={false}
            opacity={1}
          />
          <XAxis
            dataKey="name"
            type="category"
            axisLine={false}
            tickLine={false}
            tick={<CustomXAxisTick />}
            dy={10}
            padding={{ left: 20, right: 20 }}
          />
          <YAxis
            type="number"
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatCurrencyAmount(value)}
            width={30}
          />
          <Bar
            dataKey="value"
            name="Mentions"
            fill="#10B981"
            radius={[4, 4, 0, 0]}
            minPointSize={3}
          />

          <ChartTooltip
            cursor={false}
            content={
              <ChartTooltipContent
                formatter={(value, name, item) => (
                  <div className="flex flex-col">
                    <div className="flex items-center">
                      {item.payload.icon && (
                        <img
                          src={item.payload.icon}
                          alt={item.payload.fullName}
                          className="w-5 h-5 mr-2"
                        />
                      )}
                      <span className="font-medium">{item.payload.fullName}</span>
                    </div>
                    <span className="mt-1">Mentions: {value}</span>
                    <div className="mt-1 text-xs">
                      <div>Positive: {item.payload.sentimentStats.positive}</div>
                      <div>Negative: {item.payload.sentimentStats.negative}</div>
                      <div>Neutral: {item.payload.sentimentStats.neutral}</div>
                    </div>
                  </div>
                )}
              />
            }
          />
        </BarChart>
      </ChartContainer>
    </div>
  );
};

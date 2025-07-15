import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceDot,
} from "recharts";
import { format } from "date-fns";

import { Spinner } from "@/components/ui/spinner";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { useTheme } from "@/hooks/use-theme";
import { useGetSentimentDivergence } from "../api/get-sentiment-divergence";
import type { SentimentDivergenceProps } from "../types";

export const SentimentDivergenceChart = ({
  coinId,
  days = 30,
  interval = "daily",
  className,
}: SentimentDivergenceProps) => {
  const { theme } = useTheme();
  const { data, isLoading, error } = useGetSentimentDivergence(
    coinId,
    days,
    interval
  );

  const chartData = useMemo(() => {
    if (!data) return [];

    return data.map((item) => ({
      timestamp: new Date(item.timestamp),
      sentiment: item.average_sentiment,
      mentions: item.mentions,
      price: item.price,
      divergence: item.divergence,
    }));
  }, [data]);

  const chartConfig = useMemo(
    () => ({
      sentiment: {
        theme: {
          light: "#10B981", // Green for positive sentiment
          dark: "#10B981", // Keep green for positive sentiment in dark mode
        },
      },
      mentions: {
        theme: {
          light: "#6366F1", // Indigo
          dark: "#818CF8", // Lighter indigo for dark mode
        },
      },
    }),
    []
  );

  const divergenceColors = {
    bullish: "#10B981",
    bearish: "#EF4444",
  };

  // Get the effective theme (light/dark)
  const effectiveTheme =
    theme === "system"
      ? window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
      : theme;

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner size="md" />
      </div>
    );
  }

  if (error) {
    console.error("Sentiment data error:", error);
    return <div>Error loading sentiment data: {error.message}</div>;
  }

  if (!data) {
    console.log("No data received for sentiment");
    return <div>No sentiment data available</div>;
  }

  if (data.length === 0) {
    return <div>No sentiment data for the selected period</div>;
  }

  return (
    <div className={`h-full ${className}`}>
      <div className="mb-4 p-3 bg-muted/50 rounded-lg text-sm">
        <div className="font-semibold mb-2">
          Social Volume vs. Sentiment Divergence
        </div>
        <div className="text-muted-foreground space-y-1">
          <div>
            <span className="text-green-500">●</span>{" "}
            <strong>Bullish Divergence:</strong> Price falls but sentiment rises
            (potential bottom)
          </div>
          <div>
            <span className="text-red-500">●</span>{" "}
            <strong>Bearish Divergence:</strong> High social volume but declining
            sentiment (potential top)
          </div>
        </div>
      </div>
      <ChartContainer
        config={chartConfig}
        className="h-[calc(100%-120px)]"
      >
        <LineChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            opacity={0.1}
          />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => format(value, "MMM d")}
            dy={10}
          />
          <YAxis
            yAxisId="sentiment"
            domain={[-1, 1]}
            tickFormatter={(value) => value.toFixed(2)}
            label={{ value: "Sentiment", angle: -90, position: "insideLeft" }}
          />
          <YAxis
            yAxisId="mentions"
            orientation="right"
            tickFormatter={(value) => value.toString()}
            label={{ value: "Mentions", angle: 90, position: "insideRight" }}
          />
          <Tooltip
            content={
              <ChartTooltipContent
                formatter={(value, name, item) => (
                  <div className="flex flex-col gap-1">
                    <div>Date: {format(item.payload.timestamp, "MMM d, yyyy")}</div>
                    <div>
                      Sentiment: {item.payload.sentiment.toFixed(2)}
                      {item.payload.sentiment > 0
                        ? " (Bullish)"
                        : item.payload.sentiment < 0
                          ? " (Bearish)"
                          : " (Neutral)"}
                    </div>
                    <div>Mentions: {item.payload.mentions}</div>
                    {item.payload.price && (
                      <div>Price: ${item.payload.price.toLocaleString()}</div>
                    )}
                    {item.payload.divergence && (
                      <div
                        className={`font-bold ${
                          item.payload.divergence === "bullish"
                            ? "text-green-500"
                            : "text-red-500"
                        }`}
                      >
                        🚨 {item.payload.divergence.toUpperCase()} DIVERGENCE
                        <div className="text-xs font-normal mt-1">
                          {item.payload.divergence === "bullish"
                            ? "Price ↓ but sentiment ↑ - Potential bottom signal"
                            : "High volume but sentiment ↓ - Potential top signal"}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              />
            }
          />
          <Legend />
          <Line
            yAxisId="sentiment"
            type="monotone"
            dataKey="sentiment"
            name="Sentiment"
            stroke={chartConfig.sentiment.theme[effectiveTheme]}
            dot={false}
            strokeWidth={2}
          />
          <Line
            yAxisId="mentions"
            type="monotone"
            dataKey="mentions"
            name="Mentions"
            stroke={chartConfig.mentions.theme[effectiveTheme]}
            dot={false}
            strokeWidth={2}
          />
          {/* Render divergence points */}
          {chartData.map((point, index) => {
            if (!point.divergence) return null;
            return (
              <ReferenceDot
                key={index}
                x={point.timestamp.getTime()}
                y={
                  point.divergence === "bullish" ? point.sentiment : point.mentions
                }
                yAxisId={point.divergence === "bullish" ? "sentiment" : "mentions"}
                r={8}
                fill={divergenceColors[point.divergence]}
                stroke="#fff"
                strokeWidth={2}
              />
            );
          })}
        </LineChart>
      </ChartContainer>
    </div>
  );
};

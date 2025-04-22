import { useEffect, useRef, useState, ReactNode } from "react";
import {
  createChart,
  IChartApi,
  AreaSeries,
  UTCTimestamp,
  ColorType,
} from "lightweight-charts";

import { ChartDataPoint, ChartInterval, ChartPeriod } from "../types";
import { useGetChartData } from "../api";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatPrice } from "../utils";
import { cn } from "@/lib/utils";

interface PriceChartProps {
  coinId: string;
  className?: string;
  headerRight?: ReactNode;
  headerLeft?: ReactNode;
  showIntervalSelector?: boolean;
}

const TIME_PERIODS: { label: string; value: ChartPeriod }[] = [
  { label: "7D", value: 7 },
  { label: "30D", value: 30 },
  { label: "90D", value: 90 },
  { label: "180D", value: 180 },
  { label: "YTD", value: "ytd" },
  { label: "365D", value: 365 },
  { label: "MAX", value: "max" },
];

// Color constants for up and down trends
const UP_COLOR = "#33D778"; // Green for uptrend
const DOWN_COLOR = "#F23645"; // Red for downtrend
const UP_GRADIENT_TOP = "rgba(51, 215, 120, 0.4)";
const UP_GRADIENT_BOTTOM = "rgba(51, 215, 120, 0)";
const DOWN_GRADIENT_TOP = "rgba(242, 54, 69, 0.4)";
const DOWN_GRADIENT_BOTTOM = "rgba(242, 54, 69, 0)";

export const PriceChart = ({
  coinId,
  className,
  headerRight,
  headerLeft,
  showIntervalSelector = false,
}: PriceChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [chartInstance, setChartInstance] = useState<IChartApi | null>(null);
  const [chartSeries, setChartSeries] = useState<any>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<ChartPeriod>(30);
  const [interval, setInterval] = useState<ChartInterval>("daily");
  const [isUptrend, setIsUptrend] = useState<boolean>(true);

  const { data, isLoading, error } = useGetChartData({
    coinId,
    days: selectedPeriod,
    interval,
  });

  // Create chart instance
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "rgba(255, 255, 255, 0.9)",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "rgba(197, 203, 206, 0.1)" },
        horzLines: { color: "rgba(197, 203, 206, 0.1)" },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      timeScale: {
        rightOffset: 0,
        barSpacing: 12,
        fixLeftEdge: true,
        fixRightEdge: true,
        lockVisibleTimeRangeOnResize: true,
        rightBarStaysOnScroll: true,
        minBarSpacing: 5,
      },
    });

    // Apply options after chart creation
    chart.applyOptions({
      layout: {
        attributionLogo: false,
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
    });

    // Use AreaSeries instead of LineSeries for gradient fill
    const areaSeries = chart.addSeries(AreaSeries, {
      lineWidth: 2,
      crosshairMarkerVisible: true,
      lastValueVisible: true,
      lineColor: UP_COLOR,
      topColor: UP_GRADIENT_TOP,
      bottomColor: UP_GRADIENT_BOTTOM,
      priceFormat: {
        type: "custom",
        formatter: (price: number) => formatPrice(price),
      },
    });

    chart.timeScale().fitContent();

    // Add listener for timeScale visible range change
    chart.timeScale().subscribeVisibleTimeRangeChange(() => {
      // This ensures the chart stays within the data range
      const logicalRange = chart.timeScale().getVisibleLogicalRange();
      if (logicalRange !== null && chartSeries) {
        // Nothing to do here, but this can be used for handling edge cases
      }
    });

    setChartInstance(chart);
    setChartSeries(areaSeries);

    return () => {
      chart.remove();
      setChartInstance(null);
      setChartSeries(null);
    };
  }, []);

  // Resize chart on window resize
  useEffect(() => {
    const handleResize = () => {
      if (chartInstance && chartContainerRef.current) {
        chartInstance.resize(
          chartContainerRef.current.clientWidth,
          chartContainerRef.current.clientHeight
        );
        chartInstance.timeScale().fitContent();

        // Ensure content fits edge to edge after resize
        const logicalRange = chartInstance.timeScale().getVisibleLogicalRange();
        if (logicalRange !== null) {
          chartInstance.timeScale().setVisibleLogicalRange({
            from: logicalRange.from + 0.5,
            to: logicalRange.to - 0.5,
          });
        }
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [chartInstance]);

  // Update chart data when data changes
  useEffect(() => {
    if (!chartSeries || !data || !data.prices.length) return;

    const chartData = data.prices.map((point) => ({
      time: (point.timestamp / 1000) as UTCTimestamp, // convert from milliseconds to seconds
      value: point.value,
    }));

    // Determine if chart is in uptrend or downtrend
    const firstPrice = data.prices[0].value;
    const lastPrice = data.prices[data.prices.length - 1].value;
    const isUp = lastPrice >= firstPrice;
    setIsUptrend(isUp);

    // Update colors based on trend
    if (chartSeries) {
      chartSeries.applyOptions({
        lineColor: isUp ? UP_COLOR : DOWN_COLOR,
        topColor: isUp ? UP_GRADIENT_TOP : DOWN_GRADIENT_TOP,
        bottomColor: isUp ? UP_GRADIENT_BOTTOM : DOWN_GRADIENT_BOTTOM,
      });
    }

    chartSeries.setData(chartData);

    if (chartInstance) {
      chartInstance.timeScale().fitContent();

      // Remove gaps at edges by adjusting the logical range
      setTimeout(() => {
        const logicalRange = chartInstance.timeScale().getVisibleLogicalRange();
        if (logicalRange !== null) {
          chartInstance.timeScale().setVisibleLogicalRange({
            from: logicalRange.from + 0.5,
            to: logicalRange.to - 0.5,
          });
        }
      }, 50);
    }
  }, [data, chartSeries, chartInstance]);

  useEffect(() => {
    if (!chartInstance || !data) return;

    // Reset the visible range when period changes
    chartInstance.timeScale().fitContent();

    // Ensure chart stays within data bounds with no gaps
    setTimeout(() => {
      const logicalRange = chartInstance.timeScale().getVisibleLogicalRange();
      if (logicalRange !== null) {
        chartInstance.timeScale().setVisibleLogicalRange({
          from: logicalRange.from + 0.5,
          to: logicalRange.to - 0.5,
        });
      }
    }, 50);
  }, [selectedPeriod, chartInstance, data]);

  return (
    <div className={`flex flex-col h-full w-full ${className || ""}`}>
      <div className="py-2 px-3 flex items-center justify-between border-b border-border">
        {headerLeft ? (
          <div className="flex items-center">{headerLeft}</div>
        ) : (
          <div></div> /* Empty div to maintain spacing */
        )}

        <div className="flex items-center space-x-4 ml-auto">
          <div className="bg-black/80 rounded-full p-0.5 inline-flex w-fit">
            {TIME_PERIODS.map((period) => (
              <Button
                key={period.value.toString()}
                variant="ghost"
                size="sm"
                onClick={() => setSelectedPeriod(period.value)}
                className={cn(
                  "h-6 rounded-full px-2 py-0 text-xs font-medium min-w-0",
                  selectedPeriod === period.value
                    ? "bg-white text-black hover:bg-white hover:text-black pointer-events-none"
                    : "text-white/80 hover:bg-zinc-800 hover:text-white"
                )}
              >
                {period.label}
              </Button>
            ))}
          </div>

          {showIntervalSelector && (
            <Select
              value={interval}
              onValueChange={(value) => setInterval(value as ChartInterval)}
            >
              <SelectTrigger className="h-7 w-24">
                <SelectValue placeholder="Interval" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hourly">Hourly</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
              </SelectContent>
            </Select>
          )}
        </div>

        {headerRight && <div className="flex items-center ml-4">{headerRight}</div>}
      </div>
      <div className="flex-1 h-full w-full">
        {isLoading && (
          <div className="flex items-center justify-center h-full">
            <p>Loading chart data...</p>
          </div>
        )}
        {error && (
          <div className="flex items-center justify-center h-full">
            <p className="text-destructive">Failed to load chart data</p>
          </div>
        )}
        <div
          ref={chartContainerRef}
          className="w-full h-full"
        />
      </div>
    </div>
  );
};

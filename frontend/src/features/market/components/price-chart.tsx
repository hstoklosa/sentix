import { useEffect, useRef, useState } from "react";
import {
  createChart,
  IChartApi,
  AreaSeries,
  UTCTimestamp,
  ColorType,
} from "lightweight-charts";

import { Spinner } from "@/components/ui/spinner";

import { useGetChartData } from "../api";
import { ChartInterval, ChartPeriod } from "../types";
import { formatPrice } from "../utils";

type PriceChartProps = {
  coinId: string;
  className?: string;
  selectedPeriod: ChartPeriod;
  selectedInterval: ChartInterval;
};

const UP_COLOR = "#33D778"; // Green uptrend
const DOWN_COLOR = "#F23645"; // Red downtrend
const UP_GRADIENT_TOP = "rgba(51, 215, 120, 0.4)";
const UP_GRADIENT_BOTTOM = "rgba(51, 215, 120, 0)";
const DOWN_GRADIENT_TOP = "rgba(242, 54, 69, 0.4)";
const DOWN_GRADIENT_BOTTOM = "rgba(242, 54, 69, 0)";

export const PriceChart = ({
  coinId,
  className,
  selectedPeriod,
  selectedInterval,
}: PriceChartProps) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [chartInstance, setChartInstance] = useState<IChartApi | null>(null);
  const [chartSeries, setChartSeries] = useState<any>(null);

  const { data, isLoading, error } = useGetChartData({
    coinId,
    days: selectedPeriod,
    interval: selectedInterval,
  });

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "rgba(255, 255, 255, 0.9)",
        attributionLogo: false,
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      crosshair: {
        vertLine: {
          visible: true,
          labelVisible: true,
        },
        horzLine: { visible: false, labelVisible: false },
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
      crosshairMarkerBorderColor: "#FFFFFF",
      crosshairMarkerBorderWidth: 2,
      crosshairMarkerRadius: 4,
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
    const isUptrend = lastPrice >= firstPrice;

    // Update colors based on trend
    if (chartSeries) {
      chartSeries.applyOptions({
        lineColor: isUptrend ? UP_COLOR : DOWN_COLOR,
        topColor: isUptrend ? UP_GRADIENT_TOP : DOWN_GRADIENT_TOP,
        bottomColor: isUptrend ? UP_GRADIENT_BOTTOM : DOWN_GRADIENT_BOTTOM,
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
      <div className="flex-1 h-full w-full">
        {isLoading && (
          <div className="flex h-full items-center justify-center">
            <Spinner size="md" />
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

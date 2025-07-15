import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  SentimentDivergenceChart,
  TrendingCoinsChart,
} from "@/features/coins/components";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function DashboardIndexComponent() {
  const [selectedCoin, setSelectedCoin] = useState("BTC");
  const [timeRange, setTimeRange] = useState("30");

  return (
    <div className="flex flex-col h-full">
      <Tabs
        defaultValue="trending"
        className="h-full bg-card rounded-lg border"
      >
        <TabsList className="flex items-center h-[45px] p-0 w-full bg-card border-b border-border rounded-t-lg rounded-b-none overflow-hidden ">
          <TabsTrigger
            value="trending"
            className="flex-1 data-[state=active]:bg-background/10 rounded-[0] border-0"
          >
            Trending
          </TabsTrigger>
          <TabsTrigger
            value="sentiment"
            className="flex-1 data-[state=active]:bg-background/10 rounded-[0] border-0"
          >
            Sentiment Divergence
          </TabsTrigger>
        </TabsList>
        <TabsContent value="trending">
          <div className="flex-1 h-full overflow-auto">
            <TrendingCoinsChart
              limit={20}
              className="w-full"
            />
          </div>
        </TabsContent>
        <TabsContent value="sentiment">
          <div className="flex justify-center items-center gap-4 p-4 border-b border-border bg-card/50">
            <Select
              value={selectedCoin}
              onValueChange={setSelectedCoin}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select coin" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BTC">Bitcoin (BTC)</SelectItem>
                <SelectItem value="ETH">Ethereum (ETH)</SelectItem>
                <SelectItem value="BNB">Binance Coin (BNB)</SelectItem>
                <SelectItem value="XRP">Ripple (XRP)</SelectItem>
                <SelectItem value="SOL">Solana (SOL)</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={timeRange}
              onValueChange={setTimeRange}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="14">Last 14 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
                <SelectItem value="180">Last 180 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex-1 h-[calc(100%-60px)] overflow-auto p-4">
            <SentimentDivergenceChart
              coinId={selectedCoin}
              days={parseInt(timeRange)}
              interval="daily"
              className="w-full h-full"
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export const Route = createFileRoute("/_app/dashboard/")({
  component: DashboardIndexComponent,
});

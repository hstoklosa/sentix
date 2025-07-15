import { useState } from "react";
import {
  Filter as FilterIcon,
  Clock as ClockIcon,
  ChevronDownIcon,
  Coins as CoinsIcon,
  X as XIcon,
} from "lucide-react";

import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Input } from "@/components/ui/input";

import { useGetCoins } from "@/features/watchlist/api/get-coins";

interface ContentFilterProps {
  startDate?: Date;
  endDate?: Date;
  startTime?: string;
  endTime?: string;
  selectedCoins?: string[];
  onApplyFilters: (filters: {
    startDate?: Date;
    endDate?: Date;
    startTime?: string;
    endTime?: string;
    selectedCoins?: string[];
  }) => void;
  onResetFilters: () => void;
}

const ContentFilter = ({
  startDate: initialStartDate,
  endDate: initialEndDate,
  startTime: initialStartTime,
  endTime: initialEndTime,
  selectedCoins: initialSelectedCoins = [],
  onApplyFilters,
  onResetFilters,
}: ContentFilterProps) => {
  const [startDate, setStartDate] = useState<Date | undefined>(initialStartDate);
  const [endDate, setEndDate] = useState<Date | undefined>(initialEndDate);
  const [startTime, setStartTime] = useState<string | undefined>(initialStartTime);
  const [endTime, setEndTime] = useState<string | undefined>(initialEndTime);
  const [selectedCoins, setSelectedCoins] =
    useState<string[]>(initialSelectedCoins);
  const [coinSearchQuery, setCoinSearchQuery] = useState("");

  // Fetch available coins for selection
  const { data: coinsData, isLoading: isLoadingCoins } = useGetCoins();

  const handleApply = () => {
    // Create ISO strings for start and end dates with time components
    const adjustedStartDate = startDate
      ? new Date(
          startDate.getFullYear(),
          startDate.getMonth(),
          startDate.getDate(),
          startTime ? parseInt(startTime.split(":")[0]) : 0,
          startTime ? parseInt(startTime.split(":")[1]) : 0,
          0
        )
      : undefined;

    const adjustedEndDate = endDate
      ? new Date(
          endDate.getFullYear(),
          endDate.getMonth(),
          endDate.getDate(),
          endTime ? parseInt(endTime.split(":")[0]) : 23,
          endTime ? parseInt(endTime.split(":")[1]) : 59,
          59
        )
      : undefined;

    console.log("Debug: Applied filters", {
      adjustedStartDate,
      adjustedEndDate,
      startTime,
      endTime,
      selectedCoins,
    });

    onApplyFilters({
      startDate: adjustedStartDate,
      endDate: adjustedEndDate,
      startTime,
      endTime,
      selectedCoins,
    });
  };

  const handleResetFilters = () => {
    setStartDate(undefined);
    setEndDate(undefined);
    setStartTime(undefined);
    setEndTime(undefined);
    setSelectedCoins([]);
    setCoinSearchQuery("");
    onResetFilters();
  };

  const handleCoinToggle = (coinSymbol: string) => {
    setSelectedCoins((prev) =>
      prev.includes(coinSymbol)
        ? prev.filter((symbol) => symbol !== coinSymbol)
        : [...prev, coinSymbol]
    );
  };

  const handleRemoveCoin = (coinSymbol: string) => {
    setSelectedCoins((prev) => prev.filter((symbol) => symbol !== coinSymbol));
  };

  // Filter coins based on search query
  const filteredCoins =
    coinsData?.items?.filter(
      (coin) =>
        coin.symbol.toLowerCase().includes(coinSearchQuery.toLowerCase()) ||
        coin.name.toLowerCase().includes(coinSearchQuery.toLowerCase())
    ) || [];

  const hasActiveFilters =
    startDate || endDate || startTime || endTime || selectedCoins.length > 0;

  return (
    <Drawer direction="right">
      <DrawerTrigger
        className={`flex items-center gap-1 px-1.5 py-1 h-7 text-sm rounded-md border border-input hover:bg-accent whitespace-nowrap ${hasActiveFilters ? "bg-accent" : ""}`}
      >
        <FilterIcon className="size-3.5" />
        {hasActiveFilters && <span className="text-xs">•</span>}
      </DrawerTrigger>
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>Filter News</DrawerTitle>
          <DrawerDescription>
            Find content by source, date, time, and more.
          </DrawerDescription>
        </DrawerHeader>

        <div className="p-4 space-y-4">
          <div className="flex flex-col gap-3">
            <Label
              htmlFor="date"
              className="px-1"
            >
              By date
            </Label>

            <div className="flex items-center justify-between">
              <Popover modal={true}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    id="startDate"
                    className="w-36 justify-between font-normal"
                  >
                    {startDate ? startDate.toLocaleDateString() : "DD/MM/YYYY"}
                    <ChevronDownIcon className="ml-auto h-4 w-4 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="w-auto p-0"
                  align="start"
                >
                  <Calendar
                    mode="single"
                    selected={startDate}
                    captionLayout="dropdown"
                    onSelect={(date) => {
                      setStartDate(date);
                    }}
                    autoFocus
                  />
                </PopoverContent>
              </Popover>

              <div className="h-px w-5 bg-primary" />

              <Popover modal={true}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    id="endDate"
                    className="w-36 justify-between font-normal"
                  >
                    {endDate ? endDate.toLocaleDateString() : "DD/MM/YYYY"}
                    <ChevronDownIcon className="ml-auto h-4 w-4 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="w-auto p-0"
                  align="start"
                >
                  <Calendar
                    mode="single"
                    selected={endDate}
                    captionLayout="dropdown"
                    onSelect={(date) => {
                      setEndDate(date);
                    }}
                    autoFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            <Label
              htmlFor="time"
              className="px-1 mt-4"
            >
              By time
            </Label>

            <div className="flex items-center justify-between">
              <Popover modal={true}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    id="startTime"
                    className="w-36 justify-between font-normal"
                  >
                    {startTime || "HH:MM"}
                    <ClockIcon className="ml-auto h-4 w-4 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="w-auto p-0"
                  align="start"
                >
                  <input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full p-2 border rounded-md"
                  />
                </PopoverContent>
              </Popover>

              <div className="h-px w-5 bg-primary" />

              <Popover modal={true}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    id="endTime"
                    className="w-36 justify-between font-normal"
                  >
                    {endTime || "HH:MM"}
                    <ClockIcon className="ml-auto h-4 w-4 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent
                  className="w-auto p-0"
                  align="start"
                >
                  <input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full p-2 border rounded-md"
                  />
                </PopoverContent>
              </Popover>
            </div>

            <Label
              htmlFor="coins"
              className="px-1 mt-4"
            >
              By cryptocurrency
            </Label>

            {/* Coin selection dropdown */}
            <Popover modal={true}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-between font-normal"
                >
                  <div className="flex items-center gap-2">
                    <CoinsIcon className="h-4 w-4" />
                    {selectedCoins.length > 0
                      ? `${selectedCoins.length} coin${selectedCoins.length > 1 ? "s" : ""} selected`
                      : "Select coins"}
                  </div>
                  <ChevronDownIcon className="ml-auto h-4 w-4 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent
                className="w-80 p-0"
                align="start"
              >
                <div className="p-3 border-b">
                  <Input
                    placeholder="Search coins..."
                    value={coinSearchQuery}
                    onChange={(e) => setCoinSearchQuery(e.target.value)}
                    className="h-8"
                  />
                </div>
                <div className="max-h-60 overflow-y-auto">
                  {isLoadingCoins ? (
                    <div className="p-3 text-center text-sm text-muted-foreground">
                      Loading coins...
                    </div>
                  ) : filteredCoins.length > 0 ? (
                    <div className="p-1">
                      {filteredCoins.slice(0, 50).map((coin) => (
                        <div
                          key={coin.id}
                          className="flex items-center gap-2 p-2 hover:bg-accent rounded-md cursor-pointer"
                          onClick={() =>
                            handleCoinToggle(coin.symbol.toUpperCase())
                          }
                        >
                          <div className="flex items-center gap-2 flex-1">
                            {coin.image && (
                              <img
                                src={coin.image}
                                alt={coin.name}
                                className="h-6 w-6 rounded-full"
                              />
                            )}
                            <div>
                              <div className="font-medium text-sm">
                                {coin.symbol.toUpperCase()}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {coin.name}
                              </div>
                            </div>
                          </div>
                          {selectedCoins.includes(coin.symbol.toUpperCase()) && (
                            <div className="h-2 w-2 bg-primary rounded-full" />
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 text-center text-sm text-muted-foreground">
                      {coinSearchQuery ? "No coins found" : "No coins available"}
                    </div>
                  )}
                </div>
              </PopoverContent>
            </Popover>

            {/* Selected coins display */}
            {selectedCoins.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {selectedCoins.map((coinSymbol) => (
                  <div
                    key={coinSymbol}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-sm"
                  >
                    {coinSymbol}
                    <XIcon
                      className="h-3 w-3 cursor-pointer hover:text-destructive"
                      onClick={() => handleRemoveCoin(coinSymbol)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <DrawerFooter>
          <DrawerClose asChild>
            <Button onClick={handleApply}>Apply Filters</Button>
          </DrawerClose>
          <Button
            variant="outline"
            onClick={handleResetFilters}
          >
            Reset Filters
          </Button>
          <DrawerClose asChild>
            <Button variant="outline">Cancel</Button>
          </DrawerClose>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
};

export default ContentFilter;

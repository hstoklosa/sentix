import { useState } from "react";
import {
  Filter as FilterIcon,
  Calendar as CalendarIcon,
  Clock as ClockIcon,
  ChevronDownIcon,
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

interface ContentFilterProps {
  startDate?: Date;
  endDate?: Date;
  startTime?: string;
  endTime?: string;
  onApplyFilters: (filters: {
    startDate?: Date;
    endDate?: Date;
    startTime?: string;
    endTime?: string;
  }) => void;
  onResetFilters: () => void;
}

const ContentFilter = ({
  startDate: initialStartDate,
  endDate: initialEndDate,
  startTime: initialStartTime,
  endTime: initialEndTime,
  onApplyFilters,
  onResetFilters,
}: ContentFilterProps) => {
  const [startDate, setStartDate] = useState<Date | undefined>(initialStartDate);
  const [endDate, setEndDate] = useState<Date | undefined>(initialEndDate);
  const [startTime, setStartTime] = useState<string | undefined>(initialStartTime);
  const [endTime, setEndTime] = useState<string | undefined>(initialEndTime);

  const handleApply = () => {
    // Ensure start date is at beginning of day (00:00:00 UTC) and end date is at end of day (23:59:59 UTC)
    const adjustedStartDate = startDate
      ? new Date(
          Date.UTC(
            startDate.getFullYear(),
            startDate.getMonth(),
            startDate.getDate(),
            startTime ? parseInt(startTime.split(":")[0]) : 0,
            startTime ? parseInt(startTime.split(":")[1]) : 0,
            0
          )
        )
      : undefined;

    const adjustedEndDate = endDate
      ? new Date(
          Date.UTC(
            endDate.getFullYear(),
            endDate.getMonth(),
            endDate.getDate(),
            endTime ? parseInt(endTime.split(":")[0]) : 23,
            endTime ? parseInt(endTime.split(":")[1]) : 59,
            59
          )
        )
      : undefined;

    console.log("Debug: Applied date and time filters", {
      adjustedStartDate,
      adjustedEndDate,
      startTime,
      endTime,
    });

    onApplyFilters({
      startDate: adjustedStartDate,
      endDate: adjustedEndDate,
      startTime,
      endTime,
    });
  };

  const handleResetFilters = () => {
    setStartDate(undefined);
    setEndDate(undefined);
    setStartTime(undefined);
    setEndTime(undefined);
    onResetFilters();
  };

  const hasActiveFilters = startDate || endDate || startTime || endTime;

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

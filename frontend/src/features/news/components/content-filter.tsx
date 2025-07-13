import { useState } from "react";
import {
  Filter as FilterIcon,
  Calendar as CalendarIcon,
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
import { format } from "date-fns";

interface ContentFilterProps {
  startDate?: Date;
  endDate?: Date;
  onApplyFilters: (filters: { startDate?: Date; endDate?: Date }) => void;
  onResetFilters: () => void;
}

const ContentFilter = ({
  startDate: initialStartDate,
  endDate: initialEndDate,
  onApplyFilters,
  onResetFilters,
}: ContentFilterProps) => {
  const [startDate, setStartDate] = useState<Date | undefined>(initialStartDate);
  const [endDate, setEndDate] = useState<Date | undefined>(initialEndDate);

  const handleApply = () => {
    // Ensure start date is at beginning of day (00:00:00 UTC) and end date is at end of day (23:59:59 UTC)
    const adjustedStartDate = startDate
      ? new Date(
          Date.UTC(
            startDate.getFullYear(),
            startDate.getMonth(),
            startDate.getDate(),
            0,
            0,
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
            23,
            59,
            59
          )
        )
      : undefined;

    console.log("Debug: Applied date filters", {
      adjustedStartDate,
      adjustedEndDate,
    });

    onApplyFilters({
      startDate: adjustedStartDate,
      endDate: adjustedEndDate,
    });
  };

  const handleResetFilters = () => {
    setStartDate(undefined);
    setEndDate(undefined);
    onResetFilters();
  };

  const hasActiveFilters = startDate || endDate;

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
            Find content by source, date, and more.
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

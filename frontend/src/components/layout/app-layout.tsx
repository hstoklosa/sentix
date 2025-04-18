import { useRouter, Link } from "@tanstack/react-router";
import { UserRound, ChevronDown, Settings, LogOut } from "lucide-react";

import useAuth from "@/hooks/use-auth";
import { useLogout } from "@/features/auth/api/logout";
import { useWebSocketContext } from "@/features/news/context";
import { useBinanceWebSocketContext } from "@/features/coins/context";
import { cn } from "@/lib/utils";

import Logo from "../logo";
import ThemeToggle from "../theme-toggle";
import { Button } from "../ui";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "../ui/dropdown-menu";

const AppLayout = ({ children }: { children: React.ReactNode }) => {
  const router = useRouter();
  const { user } = useAuth();
  const { isConnected: isNewsConnected } = useWebSocketContext();
  const { isConnected: isBinanceConnected } = useBinanceWebSocketContext();
  const logoutMutation = useLogout({
    onSuccess: () => {
      router.invalidate().finally(() => {
        router.navigate({ to: "/" });
      });
    },
  });

  return (
    <div className="">
      <header className="flex justify-between items-center h-[56px] px-1">
        <div className="flex items-center">
          <Link
            to="/dashboard"
            className="flex items-center cursor-pointer"
          >
            <Logo className="size-8" />
            <h1 className="text-md font-[Inter] ml-1">SENTIX</h1>
          </Link>
        </div>

        <div className="flex items-center gap-1">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <div className="flex items-center group">
                <Button
                  variant="ghost"
                  size="sm"
                  className="font-normal flex items-center gap-2.5 p-2! h-9"
                >
                  <div className="flex items-center justify-center p-1.5 bg-card text-foreground rounded group-hover:bg-muted transition-colors">
                    <UserRound className="size-2.5 font-light" />
                  </div>
                  {user?.username}
                  <ChevronDown className="size-3.5 text-foreground" />
                </Button>
              </div>
            </DropdownMenuTrigger>

            <DropdownMenuContent
              align="end"
              side="bottom"
              sideOffset={10}
              className="w-[250px]"
            >
              <DropdownMenuLabel className="cursor-default">
                <p className="text-sm font-normal text-foreground truncate">
                  {user?.username}
                </p>
                <p className="text-sm font-normal text-muted-foreground truncate">
                  {user?.email}
                </p>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="flex justify-between items-center cursor-pointer"
                disabled
              >
                <span>Settings</span>
                <Settings className="size-4 ml-auto" />
              </DropdownMenuItem>
              <div className="flex justify-between items-center px-2 py-1.5 text-sm text-foreground cursor-default">
                <span>Theme</span>
                <ThemeToggle />
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="flex justify-between items-center cursor-pointer"
                onClick={() => logoutMutation.mutate(undefined)}
              >
                <span>Logout</span>
                <LogOut className="size-4 ml-auto" />
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="ml-2 flex items-center space-x-2">
            {/* News WebSocket indicator */}
            <div className="flex items-center">
              <span
                className={cn(
                  "inline-block w-2 h-2 rounded-full",
                  isNewsConnected ? "bg-chart-2" : "bg-destructive"
                )}
                title={
                  isNewsConnected
                    ? "Connected to news feed"
                    : "Disconnected from news feed"
                }
              />
              <span className="text-xs ml-1 text-muted-foreground">News</span>
            </div>

            {/* Binance WebSocket indicator */}
            <div className="flex items-center">
              <span
                className={cn(
                  "inline-block w-2 h-2 rounded-full",
                  isBinanceConnected ? "bg-chart-2" : "bg-destructive"
                )}
                title={
                  isBinanceConnected
                    ? "Connected to price feed"
                    : "Disconnected from price feed"
                }
              />
              <span className="text-xs ml-1 text-muted-foreground">Prices</span>
            </div>
          </div>
        </div>
      </header>

      <main>{children}</main>
    </div>
  );
};

export default AppLayout;

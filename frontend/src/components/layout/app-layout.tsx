import { useRouter, Link } from "@tanstack/react-router";
import { ChevronDown, Settings, LogOut } from "lucide-react";

import sentixLogo from "@/assets/sentix-logo.png";
import useAuth from "@/hooks/use-auth";
import { useLogout } from "@/features/auth/api/logout";

import { Button } from "../ui";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "../ui/dropdown-menu";
import ThemeToggle from "../theme-toggle";

const AppLayout = ({ children }: { children: React.ReactNode }) => {
  const router = useRouter();
  const { user } = useAuth();
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
        <Link
          to="/dashboard"
          className="flex items-center cursor-pointer"
        >
          <img
            src={sentixLogo}
            alt="Sentix Logo"
            className="h-8"
          />
          <h1 className="text-md font-[Inter] ml-0.5">SENTIX</h1>
        </Link>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <div className="flex items-center">
              <Button
                variant="ghost"
                size="sm"
                className="flex items-center gap-1.5"
              >
                {user?.username}
                <ChevronDown className="size-4 text-foreground" />
              </Button>
            </div>
          </DropdownMenuTrigger>

          <DropdownMenuContent
            align="end"
            side="bottom"
            sideOffset={12}
          >
            <DropdownMenuLabel className="cursor-default">
              <p className="text-sm font-normal text-foreground">
                {user?.username}
              </p>
              <p className="text-sm font-normal text-muted-foreground">
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
            <div className="flex justify-between items-center px-2 py-2 text-sm text-foreground">
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
      </header>

      <main>{children}</main>
    </div>
  );
};

export default AppLayout;

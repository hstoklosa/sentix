import { useRouter, Link } from "@tanstack/react-router";
import { ChevronDown, Settings, LogOut } from "lucide-react";

import useAuth from "@/hooks/use-auth";
import { useLogout } from "@/features/auth/api/logout";

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
          <Logo className="size-8" />
          <h1 className="text-md font-[Inter] ml-1">SENTIX</h1>
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
      </header>

      <main>{children}</main>
    </div>
  );
};

export default AppLayout;

import { useRouter } from "@tanstack/react-router";

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

const AppLayout = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  const router = useRouter();

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
          <img
            src={sentixLogo}
            alt="Sentix Logo"
            className="h-8"
          />
          <h1 className="text-sm font-[Inter] ml-1">SENTIX</h1>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <div className="flex items-center">
              <Button
                variant="ghost"
                size="sm"
              >
                {user?.username}
              </Button>
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            side="bottom"
            sideOffset={12}
          >
            <DropdownMenuLabel>
              <p className="text-sm font-normal text-foreground">
                {user?.username}
              </p>
              <p className="text-sm font-normal text-muted-foreground">
                {user?.email}
              </p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => logoutMutation.mutate(undefined)}>
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      <main>{children}</main>
    </div>
  );
};

export default AppLayout;

import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { GalleryVerticalEnd } from "lucide-react";
import { z } from "zod";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import LoginForm from "@/features/auth/components/login-form";

const Login = () => {
  const navigate = Route.useNavigate();

  return (
    <div className="h-full w-auto flex flex-col items-center justify-center">
      <div className="flex flex-col items-center gap-2">
        <Link
          to="/"
          className="flex flex-col items-center gap-2 font-medium"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-md">
            <GalleryVerticalEnd className="size-6" />
          </div>
          <span className="sr-only">SentiX</span>
        </Link>
        <h1 className="text-xl font-bold">Welcome back</h1>
        <div className="text-center text-sm">
          Don&apos;t have an account?{" "}
          <Link
            to="/register"
            className={cn(
              buttonVariants({ variant: "link" }),
              "underline underline-offset-4 p-0 h-auto"
            )}
          >
            Sign up
          </Link>
        </div>
      </div>

      <LoginForm onSuccess={() => navigate({ to: "/dashboard" })} />
    </div>
  );
};

export const Route = createFileRoute("/(auth)/login")({
  validateSearch: z.object({
    redirect: z.string().optional().catch(""),
  }),
  beforeLoad: ({ context, search }) => {
    if (context.auth.status === "AUTHENTICATED")
      throw redirect({ to: search.redirect || "/dashboard" });
  },
  component: Login,
});

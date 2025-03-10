import { createFileRoute, Link } from "@tanstack/react-router";
import { GalleryVerticalEnd } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { RegisterForm } from "@/features/auth/components/register-form";

const Register = () => {
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

        <h1 className="text-xl font-bold">Welcome to Sentix</h1>
        <div className="text-center text-sm">
          Already have an account?{" "}
          <Link
            to="/login"
            className={cn(
              buttonVariants({ variant: "link" }),
              "underline underline-offset-4 p-0 h-auto"
            )}
          >
            Sign in
          </Link>
        </div>
      </div>

      <RegisterForm className="mt-6 w-[400px]" />
    </div>
  );
};

export const Route = createFileRoute("/(auth)/register")({
  component: Register,
});

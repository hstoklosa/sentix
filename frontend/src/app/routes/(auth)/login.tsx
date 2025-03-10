import { createFileRoute } from "@tanstack/react-router";
import { GalleryVerticalEnd } from "lucide-react";

import { LoginForm } from "@/features/auth/components/login-form";

const Login = () => {
  return (
    <div className="h-full w-auto flex flex-col items-center justify-center">
      <div className="flex flex-col items-center gap-2">
        <a
          href="/"
          className="flex flex-col items-center gap-2 font-medium"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-md">
            <GalleryVerticalEnd className="size-6" />
          </div>
          <span className="sr-only">SentiX</span>
        </a>
        <h1 className="text-xl font-bold">Welcome back</h1>
        <div className="text-center text-sm">
          Don&apos;t have an account?{" "}
          <a
            href="/register"
            className="underline underline-offset-4"
          >
            Sign up
          </a>
        </div>
      </div>

      <LoginForm className="mt-8 w-[400px]" />
    </div>
  );
};

export const Route = createFileRoute("/(auth)/login")({
  component: Login,
});

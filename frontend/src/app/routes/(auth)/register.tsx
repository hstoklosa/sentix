import { createFileRoute } from "@tanstack/react-router";
import { GalleryVerticalEnd } from "lucide-react";

import { RegisterForm } from "@/features/auth/components/register-form";

const Register = () => {
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
        <h1 className="text-xl font-bold">Welcome to SentiX</h1>
        <div className="text-center text-sm">
          Already have an account?{" "}
          <a
            href="/login"
            className="underline underline-offset-4"
          >
            Sign in
          </a>
        </div>
      </div>

      <RegisterForm className="mt-6 w-[400px]" />
    </div>
  );
};

export const Route = createFileRoute("/(auth)/register")({
  component: Register,
});

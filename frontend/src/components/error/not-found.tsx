import { useRouterState, Link, useRouter } from "@tanstack/react-router";

import { DotPattern, Button } from "../ui";

const NotFound = () => {
  const { location } = useRouterState();
  const { history } = useRouter();

  return (
    <div className="flex min-h-[100dvh] flex-col items-center justify-center text-center">
      <DotPattern />

      <div className="space-y-6 px-4">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl">404</h1>
          <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">
            Page not found
          </h2>
          <p className="mx-auto max-w-[500px] text-muted-foreground">
            We couldn't find the page you were looking for at{" "}
            <span className="font-medium text-foreground">{location.pathname}</span>
            . The page might have been moved or deleted.
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-2">
          <Button
            variant="outline"
            onClick={() => history.go(-1)}
          >
            Go Back
          </Button>
          <Button asChild>
            <Link to="/">Go Home</Link>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
